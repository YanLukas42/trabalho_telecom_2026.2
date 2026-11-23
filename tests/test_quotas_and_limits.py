import io
from pathlib import Path
import pytest

from telecom.accounts.models import Principal, Tenant, User
from telecom.diarization.pipeline import DiarizationOutputs
from telecom.lessons.materials import LessonMaterials, validated_materials
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UsageRepository, UserRepository
from telecom.web.jobs import (
    ConcurrencyLimitError,
    DurationLimitError,
    JobOptions,
    JobService,
    QuotaExceededError,
    UploadLimitError,
)
from tests.test_web_jobs import ImmediateExecutor


class FakeChunkStream:
    """Simula um stream que envia chunks gigantes para testar limite de 300 MB."""
    def __init__(self, total_bytes: int, chunk_size: int = 1024 * 1024):
        self.remaining = total_bytes
        self.chunk_size = chunk_size

    def read(self, size: int = -1):
        if self.remaining <= 0:
            return b""
        n = min(self.remaining, self.chunk_size)
        self.remaining -= n
        return b"A" * n


class FakePipeline:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def run(self, source: Path):
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        rep_json = reports_dir / f"{source.stem}_diarizacao_pydantic.json"
        rep_json.write_text('{"segmentos": []}', encoding="utf-8")
        return DiarizationOutputs(
            payload={"duracao_original_segundos": 120.0, "metricas_tokens": {"total_tokens": 450}, "segmentos": []},
            report_json=rep_json,
            report_md=reports_dir / f"{source.stem}_diarizacao_pydantic.md",
            words_json=reports_dir / f"{source.stem}_palavra_por_palavra.json",
            words=None,
        )


def make_service(tmp_path: Path, duration_sec: float = 60.0):
    db = Database(tmp_path / "test.db")
    session_repo = SessionRepository(db)
    user_repo = UserRepository(db)
    usage_repo = UsageRepository(db)

    user_repo.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=60))
    user_repo.save_user(User("prof-1", "escola-1", "p1@alpha.com", "Prof 1", "hash", "teacher"))
    user_repo.save_user(User("prof-2", "escola-1", "p2@alpha.com", "Prof 2", "hash", "teacher"))
    user_repo.save_user(User("prof-3", "escola-1", "p3@alpha.com", "Prof 3", "hash", "teacher"))

    service = JobService(
        pipeline_factory=lambda opt, out: FakePipeline(out),
        session_repo=session_repo,
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
        duration_prober=lambda path: duration_sec,
        user_repo=user_repo,
        usage_repo=usage_repo,
    )
    return service, session_repo, usage_repo, db


def test_upload_exceeding_300mb_is_aborted_and_cleaned(tmp_path):
    service, _, _, _ = make_service(tmp_path)
    principal = Principal("escola-1", "prof-1", "teacher")

    # 301 MB stream
    oversized = FakeChunkStream(total_bytes=301 * 1024 * 1024)

    with pytest.raises(UploadLimitError, match="ultrapassa o limite de 300 MB"):
        service.submit(principal, "grande.mp3", oversized, JobOptions())

    # Garante que nenhum arquivo ou pasta órfã foi deixada
    tenant_dir = tmp_path / "jobs" / "escola-1" / "sessions"
    if tenant_dir.exists():
        assert list(tenant_dir.iterdir()) == []


def test_duration_exceeding_3_hours_is_rejected_and_cleaned(tmp_path):
    # 3h e 1 segundo (10801 s)
    service, _, _, _ = make_service(tmp_path, duration_sec=10801.0)
    principal = Principal("escola-1", "prof-1", "teacher")

    with pytest.raises(DurationLimitError, match="excede a duração máxima permitida de 3 horas"):
        service.submit(principal, "longo.mp3", io.BytesIO(b"audio"), JobOptions())

    # Garante limpeza
    tenant_dir = tmp_path / "jobs" / "escola-1" / "sessions"
    if tenant_dir.exists():
        assert list(tenant_dir.iterdir()) == []


def test_monthly_quota_exceeded_raises_429_format(tmp_path):
    service, _, usage_repo, _ = make_service(tmp_path, duration_sec=900.0)  # 15 minutos
    principal = Principal("escola-1", "prof-1", "teacher")

    # Tenant tem cota de 60 min. Registra 50 min de uso no mês atual:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    usage_repo.record("escola-1", "sess-antiga", "transcription", audio_seconds=3000.0, tokens=100)

    # 50 min usados + 15 min do novo áudio = 65 min > 60 min
    with pytest.raises(QuotaExceededError) as exc_info:
        service.submit(principal, "nova_aula.mp3", io.BytesIO(b"audio"), JobOptions())

    msg = str(exc_info.value)
    assert "Sua escola usou 50 de 60 minutos este mês." in msg
    assert "Renova em 01/" in msg


def test_active_session_limits_per_teacher_and_school(tmp_path):
    service, session_repo, _, _ = make_service(tmp_path)
    prof1 = Principal("escola-1", "prof-1", "teacher")
    prof2 = Principal("escola-1", "prof-2", "teacher")
    prof3 = Principal("escola-1", "prof-3", "teacher")

    # Simula prof1 com uma aula ativa (queued)
    session_repo.save("escola-1", {
        "id": "ativa-1", "tenant_id": "escola-1", "teacher_id": "prof-1",
        "file_name": "a.mp3", "status": "processing",
    })

    # Prof 1 tenta submeter outra aula -> bloqueado por limite do professor
    with pytest.raises(ConcurrencyLimitError, match="Você já possui uma aula em processamento. Espere a aula anterior terminar."):
        service.submit(prof1, "aula2.mp3", io.BytesIO(b"audio"), JobOptions())

    # Simula prof2 com uma aula ativa (agora a escola tem 2 ativas)
    session_repo.save("escola-1", {
        "id": "ativa-2", "tenant_id": "escola-1", "teacher_id": "prof-2",
        "file_name": "b.mp3", "status": "queued",
    })

    # Prof 3 tenta submeter -> bloqueado por limite da escola (máximo 2 ativas)
    with pytest.raises(ConcurrencyLimitError, match="Sua escola já possui 2 aulas em processamento. Espere a aula anterior terminar."):
        service.submit(prof3, "aula3.mp3", io.BytesIO(b"audio"), JobOptions())


def test_usage_events_recorded_after_transcription(tmp_path):
    service, _, usage_repo, db = make_service(tmp_path, duration_sec=120.0)
    principal = Principal("escola-1", "prof-1", "teacher")

    job = service.submit(principal, "aula.mp3", io.BytesIO(b"audio"), JobOptions())
    assert job.status.value == "done"

    # Verifica gravação em usage_events
    with db.connection() as conn:
        row = conn.execute(
            "SELECT * FROM usage_events WHERE tenant_id = ? AND session_id = ? AND kind = 'transcription'",
            ("escola-1", job.id),
        ).fetchone()
        assert row is not None
        assert row["audio_seconds"] == 120.0
        assert row["tokens"] == 450
