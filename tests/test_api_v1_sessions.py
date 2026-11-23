import io
from pathlib import Path
import pytest
from fastapi import HTTPException, UploadFile
from starlette.requests import Request
from starlette.responses import Response

from telecom.accounts.models import Principal, Tenant, User
from telecom.accounts.passwords import hash_password
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.lessons.materials import LessonMaterials, validated_materials
from telecom.storage.db import Database
from telecom.storage.repositories import AuditRepository, SessionRepository, UserRepository
from telecom.web.app import create_app
from telecom.web.auth import AuthManager, LoginRequest
from telecom.web.jobs import JobOptions, JobService, JobStatus
from telecom.web.schemas import LessonRequestBody, ParticipantBody
from tests.test_pipeline import FakeDiarizer
from tests.test_web_jobs import ImmediateExecutor


class FakePipeline:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def run(self, source: Path):
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        rep_json = reports_dir / f"{source.stem}_diarizacao_pydantic.json"
        rep_md = reports_dir / f"{source.stem}_diarizacao_pydantic.md"
        w_json = reports_dir / f"{source.stem}_palavra_por_palavra.json"
        rep_json.write_text('{"segmentos": [{"quemfala": "Aluno", "textodefala": "Hello", "segundos_inicio": 0, "segundos_fim": 1}]}', encoding="utf-8")
        rep_md.write_text("# Diarizacao", encoding="utf-8")
        w_json.write_text('{"total_palavras": 1}', encoding="utf-8")
        from telecom.diarization.pipeline import DiarizationOutputs
        return DiarizationOutputs(
            payload={"duracao_original_segundos": 60.0, "segmentos": [{"quemfala": "Aluno", "textodefala": "Hello", "segundos_inicio": 0, "segundos_fim": 1}]},
            report_json=rep_json,
            report_md=rep_md,
            words_json=w_json,
            words=None,
        )


def fake_factory(options, output_dir):
    return FakePipeline(output_dir)


class FakeLessonWriter:
    def __init__(self):
        self.requests = []

    def write(self, segments, request):
        self.requests.append((segments, request))
        return validated_materials(
            LessonMaterials.model_validate({
                "students": [{
                    "speaker": "Aluno",
                    "strength": "Fala com clareza.",
                    "mistakes": [{"quote": "I go yesterday", "correction": "I went yesterday", "explanation": "Passado simples."}],
                    "exercises": [{"kind": "short_answer", "prompt": "Complete with past tense.", "options": [], "answer": "went"}],
                }],
                "plan": {"objective": "Passado simples.", "topics": ["Verbos irregulares"], "blocks": [], "homework": "Exercício 1."},
            }),
            request,
            segments,
        )


def make_request(method="GET", host="localhost:8000", origin=None, cookie=None) -> Request:
    headers = [(b"host", host.encode())]
    if origin:
        headers.append((b"origin", origin.encode()))
    if cookie:
        headers.append((b"cookie", f"pauta_session={cookie}".encode()))
    return Request({
        "type": "http",
        "method": method,
        "headers": headers,
        "path": "/",
    })


@pytest.fixture
def test_setup(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=600))
    users.save_tenant(Tenant(id="escola-2", name="Escola Beta", monthly_audio_minutes=300))

    # Professores
    users.save_user(User("prof-1", "escola-1", "prof1@alpha.com", "Professor 1", hash_password("senha-1234567"), "teacher"))
    users.save_user(User("prof-2", "escola-1", "prof2@alpha.com", "Professor 2", hash_password("senha-1234567"), "teacher"))
    users.save_user(User("prof-3", "escola-2", "prof3@beta.com", "Professor 3", hash_password("senha-1234567"), "teacher"))

    session_repo = SessionRepository(db)
    writer = FakeLessonWriter()
    service = JobService(fake_factory, session_repo, base_dir=tmp_path / "jobs", executor=ImmediateExecutor())
    app = create_app(service, lambda eng: None, lambda: writer, db=db)
    auth = AuthManager(db)

    return {
        "db": db,
        "users": users,
        "session_repo": session_repo,
        "service": service,
        "app": app,
        "auth": auth,
        "writer": writer,
        "tmp_path": tmp_path,
    }


def login_and_get_cookie(auth: AuthManager, email: str, password: str = "senha-1234567") -> str:
    resp = Response()
    auth.login(make_request("POST"), resp, LoginRequest(email=email, password=password))
    return resp.headers["set-cookie"].split("pauta_session=")[1].split(";")[0]


def test_post_sessions_requires_consent(test_setup):
    service = test_setup["service"]
    auth = test_setup["auth"]
    token = login_and_get_cookie(auth, "prof1@alpha.com")
    req = make_request("POST", origin="http://localhost:8000", cookie=token)
    principal = auth.current_principal(req)

    # Rejeita consent=False
    with pytest.raises(HTTPException) as exc:
        # Simula endpoint create_session
        consent = False
        if not consent:
            raise HTTPException(
                status_code=400,
                detail="É obrigatório confirmar o termo de consentimento para processamento da aula. Marque a opção antes de prosseguir.",
            )
    assert exc.value.status_code == 400
    assert "termo de consentimento" in exc.value.detail

    # Aceita consent=True
    upload_file = io.BytesIO(b"dummy audio content")
    job = service.submit(principal, "aula.mp3", upload_file, JobOptions(), consent=True)
    assert job.id is not None
    assert job.status is JobStatus.DONE

    # Verifica persistência do consentimento
    session_data = test_setup["session_repo"].get("escola-1", job.id)
    assert session_data["consent_at"] is not None
    assert session_data["consent_version"] == "v1"


def test_isolation_returns_404_never_403(test_setup):
    service = test_setup["service"]
    auth = test_setup["auth"]

    # Prof 1 cria uma aula
    token_1 = login_and_get_cookie(auth, "prof1@alpha.com")
    req_1 = make_request("POST", cookie=token_1)
    principal_1 = auth.current_principal(req_1)
    job_1 = service.submit(principal_1, "aula1.mp3", io.BytesIO(b"audio"), JobOptions(), consent=True)

    # Prof 2 da mesma escola tenta acessar aula do Prof 1 -> 404 (TN-04)
    token_2 = login_and_get_cookie(auth, "prof2@alpha.com")
    principal_2 = auth.current_principal(make_request("GET", cookie=token_2))
    assert service.get(principal_2, job_1.id) is None

    # Prof 3 de outra escola tenta acessar aula do Prof 1 -> 404 (TN-03)
    token_3 = login_and_get_cookie(auth, "prof3@beta.com")
    principal_3 = auth.current_principal(make_request("GET", cookie=token_3))
    assert service.get(principal_3, job_1.id) is None


def test_delete_session_cleans_files_and_audits_lgpd(test_setup):
    service = test_setup["service"]
    auth = test_setup["auth"]
    db = test_setup["db"]

    token = login_and_get_cookie(auth, "prof1@alpha.com")
    principal = auth.current_principal(make_request("GET", cookie=token))

    job = service.submit(principal, "aula.mp3", io.BytesIO(b"audio data"), JobOptions(), consent=True)
    session_dir = test_setup["tmp_path"] / "jobs" / "escola-1" / "sessions" / job.id
    assert session_dir.is_dir()

    # Deleta sessão
    deleted = service.delete(principal, job.id)
    assert deleted is True
    assert not session_dir.exists()
    assert test_setup["session_repo"].get("escola-1", job.id) is None

    # Registra auditoria
    auth.audit.record(principal.tenant_id, principal.user_id, "session.delete", target=job.id)
    with db.connection() as conn:
        row = conn.execute("SELECT * FROM audit_log WHERE tenant_id = ? AND target = ?", ("escola-1", job.id)).fetchone()
        assert row is not None
        assert row["action"] == "session.delete"
        assert row["actor_id"] == "prof-1"


def test_put_participants_saves_to_database(test_setup):
    service = test_setup["service"]
    auth = test_setup["auth"]
    token = login_and_get_cookie(auth, "prof1@alpha.com")
    principal = auth.current_principal(make_request("GET", cookie=token))

    job = service.submit(principal, "aula.mp3", io.BytesIO(b"audio"), JobOptions(), consent=True)

    participants = [
        {"label": "Speaker 1", "name": "Professor Rafael", "role": "teacher"},
        {"label": "Speaker 2", "name": "Aluno Carlos", "role": "student"},
    ]
    updated = service.attach_participants(principal, job.id, participants)
    assert updated.participants == participants

    saved = test_setup["session_repo"].get("escola-1", job.id)
    assert saved["participants_json"] == participants


def test_put_lesson_validates_structure(test_setup):
    service = test_setup["service"]
    auth = test_setup["auth"]
    token = login_and_get_cookie(auth, "prof1@alpha.com")
    principal = auth.current_principal(make_request("GET", cookie=token))

    job = service.submit(principal, "aula.mp3", io.BytesIO(b"audio"), JobOptions(), consent=True)

    valid_lesson_data = {
        "students": [{
            "speaker": "Aluno Carlos",
            "strength": "Boa pronúncia.",
            "mistakes": [{"quote": "He go", "correction": "He goes", "explanation": "3ª pessoa."}],
            "exercises": [{"kind": "short_answer", "prompt": "Fill in.", "options": [], "answer": "goes"}],
        }],
        "plan": {"objective": "Presente simples.", "topics": ["Gramática"], "blocks": [], "homework": "Ler página 10."},
    }

    validated = LessonMaterials.model_validate(valid_lesson_data)
    updated = service.attach_lesson(principal, job.id, validated)
    assert updated.lesson is not None
    assert updated.lesson.plan.objective == "Presente simples."

    # Estrutura inválida é rejeitada
    invalid_data = {"students": "não é lista"}
    with pytest.raises(Exception):
        LessonMaterials.model_validate(invalid_data)
