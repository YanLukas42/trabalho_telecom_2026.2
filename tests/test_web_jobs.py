import io
from pathlib import Path

import pytest

from telecom.accounts.models import Principal, Tenant, User
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UserRepository
from telecom.web.jobs import JobOptions, JobService, JobStatus, UNEXPECTED_ERROR_MESSAGE, sanitize_filename
from tests.conftest import requires_ffmpeg
from tests.test_pipeline import FakeDiarizer

PRINCIPAL_A = Principal(tenant_id="tenant-1", user_id="user-1", role="teacher")
PRINCIPAL_B = Principal(tenant_id="tenant-1", user_id="user-2", role="teacher")
PRINCIPAL_OTHER_TENANT = Principal(tenant_id="tenant-2", user_id="user-3", role="teacher")
PRINCIPAL_OWNER = Principal(tenant_id="tenant-1", user_id="user-admin", role="owner")


class ImmediateExecutor:
    """Roda o job na hora, na mesma thread: o teste não precisa esperar."""

    def submit(self, fn, *args):
        fn(*args)


def fake_factory(options, output_dir):
    return DiarizationPipeline(FakeDiarizer(), DiarizationOptions(compact_silence=options.compact_silence), output_dir)


def failing_factory(error):
    def factory(options, output_dir):
        raise error
    return factory


def make_service(tmp_path: Path, factory=fake_factory) -> JobService:
    db = Database(tmp_path / "test.db")
    repo = SessionRepository(db)
    users = UserRepository(db)
    users.save_tenant(Tenant(id="tenant-1", name="Escola Alpha"))
    users.save_tenant(Tenant(id="tenant-2", name="Escola Beta"))
    users.save_user(User("user-1", "tenant-1", "u1@alpha.com", "User 1", "hash", "teacher"))
    users.save_user(User("user-2", "tenant-1", "u2@alpha.com", "User 2", "hash", "teacher"))
    users.save_user(User("user-3", "tenant-2", "u3@beta.com", "User 3", "hash", "teacher"))
    users.save_user(User("user-admin", "tenant-1", "admin@alpha.com", "Admin", "hash", "owner"))
    return JobService(factory, repo, base_dir=tmp_path / "jobs", executor=ImmediateExecutor())


def test_sanitize_filename_strips_paths_and_odd_chars():
    assert sanitize_filename("../../etc/aula de hoje.mp3") == "aula_de_hoje.mp3"
    assert sanitize_filename("C:\\fakepath\\áudio.wav".split("\\")[-1]) == "áudio.wav"
    with pytest.raises(ValueError):
        sanitize_filename("...")


def test_rejects_unsupported_extension(tmp_path):
    service = make_service(tmp_path)
    with pytest.raises(ValueError, match="Formato não suportado"):
        service.submit(PRINCIPAL_A, "notas.txt", io.BytesIO(b"x"), JobOptions())
    assert service.list(PRINCIPAL_A) == []


def test_rejects_empty_file_and_cleans_up(tmp_path):
    service = make_service(tmp_path)
    with pytest.raises(ValueError, match="vazio"):
        service.submit(PRINCIPAL_A, "aula.mp3", io.BytesIO(b""), JobOptions())
    assert service.list(PRINCIPAL_A) == []


@requires_ffmpeg
def test_job_runs_pipeline_and_keeps_outputs(speech_wav, tmp_path):
    service = make_service(tmp_path)
    with speech_wav.open("rb") as handle:
        job = service.submit(PRINCIPAL_A, "speech.wav", handle, JobOptions(compact_silence=True))

    assert job.status is JobStatus.DONE
    assert job.source.is_relative_to(tmp_path / "jobs" / "tenant-1" / "sessions" / job.id)
    assert job.outputs.payload["vad_aplicado"] is True
    assert job.finished_at >= job.started_at


def test_known_errors_keep_their_message(tmp_path):
    service = make_service(tmp_path, failing_factory(ValueError("Arquivo grande demais")))
    job = service.submit(PRINCIPAL_A, "aula.mp3", io.BytesIO(b"abc"), JobOptions())
    assert job.status is JobStatus.FAILED
    assert job.error == "Arquivo grande demais"


def test_unexpected_errors_are_hidden_from_the_user(tmp_path):
    service = make_service(tmp_path, failing_factory(RuntimeError("stack interna")))
    job = service.submit(PRINCIPAL_A, "aula.mp3", io.BytesIO(b"abc"), JobOptions())
    assert job.status is JobStatus.FAILED
    assert job.error == UNEXPECTED_ERROR_MESSAGE


def test_list_is_newest_first(tmp_path):
    service = make_service(tmp_path, failing_factory(ValueError("x")))
    first = service.submit(PRINCIPAL_A, "a.mp3", io.BytesIO(b"1"), JobOptions())
    second = service.submit(PRINCIPAL_A, "b.mp3", io.BytesIO(b"2"), JobOptions())
    assert [job.id for job in service.list(PRINCIPAL_A)] == [second.id, first.id]


def test_tenant_and_teacher_isolation(tmp_path):
    service = make_service(tmp_path, failing_factory(ValueError("x")))
    job_a = service.submit(PRINCIPAL_A, "a.mp3", io.BytesIO(b"1"), JobOptions())

    # Outro professor do mesmo tenant não vê a aula (TN-04)
    assert service.get(PRINCIPAL_B, job_a.id) is None
    assert service.list(PRINCIPAL_B) == []

    # Outro tenant não vê
    assert service.get(PRINCIPAL_OTHER_TENANT, job_a.id) is None
    assert service.list(PRINCIPAL_OTHER_TENANT) == []

    # Coordenador / Owner do mesmo tenant vê
    assert service.get(PRINCIPAL_OWNER, job_a.id) is not None
    assert len(service.list(PRINCIPAL_OWNER)) == 1


def test_recovers_active_jobs_on_startup(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = SessionRepository(db)
    users = UserRepository(db)
    users.save_tenant(Tenant(id="tenant-1", name="Escola Alpha"))
    users.save_user(User("user-1", "tenant-1", "u1@alpha.com", "User 1", "hash", "teacher"))
    repo.save("tenant-1", {
        "id": "job-hung", "tenant_id": "tenant-1", "teacher_id": "user-1",
        "filename": "a.mp3", "original_filename": "a.mp3", "engine": "gemini",
        "status": "processing",
    })

    # Subida do serviço recupera jobs pendentes (ADR-0003)
    service = JobService(fake_factory, repo, base_dir=tmp_path / "jobs", executor=ImmediateExecutor())
    recovered = service.get(PRINCIPAL_A, "job-hung")
    assert recovered is not None
    assert recovered.status is JobStatus.FAILED
    assert "servidor reiniciou" in recovered.error


def test_retry_reprocesses_failed_session_and_enforces_guards(tmp_path):
    from telecom.diarization.pipeline import DiarizationOutputs
    from telecom.web.jobs import ConcurrencyLimitError

    state = {"should_fail": True}

    class SwitchablePipeline:
        def __init__(self, out_dir: Path):
            self.out_dir = out_dir

        def run(self, source: Path) -> DiarizationOutputs:
            if state["should_fail"]:
                raise ValueError("API sobrecarregada")
            reports = self.out_dir / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            rep_json = reports / f"{source.stem}_diarizacao_pydantic.json"
            rep_md = reports / f"{source.stem}_diarizacao_pydantic.md"
            w_json = reports / f"{source.stem}_palavra_por_palavra.json"
            rep_json.write_text('{"segmentos": []}', encoding="utf-8")
            rep_md.write_text("# OK", encoding="utf-8")
            w_json.write_text("{}", encoding="utf-8")
            return DiarizationOutputs(
                payload={"duracao_original_segundos": 30.0, "metricas_tokens": {"total_tokens": 50}, "segmentos": []},
                report_json=rep_json,
                report_md=rep_md,
                words_json=w_json,
                words=None,
            )

    service = make_service(tmp_path, lambda opts, out: SwitchablePipeline(out))
    failed_job = service.submit(PRINCIPAL_A, "aula.mp3", io.BytesIO(b"audio"), JobOptions())
    assert failed_job.status is JobStatus.FAILED
    assert failed_job.error == "API sobrecarregada"

    # Outro professor não pode dar retry
    with pytest.raises(ValueError, match="não encontrada"):
        service.retry(PRINCIPAL_B, failed_job.id)

    # Reprocessa com sucesso após falha
    state["should_fail"] = False
    retried = service.retry(PRINCIPAL_A, failed_job.id)
    assert retried.status is JobStatus.DONE
    assert retried.error is None

    # Arquivo removido no disco -> erro claro ao tentar de novo
    retried.source.unlink()
    with pytest.raises(ValueError, match="não está mais disponível"):
        service.retry(PRINCIPAL_A, retried.id)

    # Sessão ativa não pode ser reenviada
    service._repo.update_status(PRINCIPAL_A.tenant_id, retried.id, JobStatus.PROCESSING.value)
    with pytest.raises(ValueError, match="já está em processamento"):
        service.retry(PRINCIPAL_A, retried.id)

    # Se outra aula do mesmo professor estiver ativa, respeita limite de concorrência
    service._repo.save(PRINCIPAL_A.tenant_id, {
        "id": "outra-ativa", "tenant_id": PRINCIPAL_A.tenant_id, "teacher_id": PRINCIPAL_A.user_id,
        "file_name": "x.mp3", "status": "queued",
    })
    another_failed = service.get(PRINCIPAL_A, retried.id)
    assert another_failed is not None
    service._repo.update_status(PRINCIPAL_A.tenant_id, retried.id, JobStatus.FAILED.value)
    retried.source.write_bytes(b"audio")
    with pytest.raises(ConcurrencyLimitError):
        service.retry(PRINCIPAL_A, retried.id)
