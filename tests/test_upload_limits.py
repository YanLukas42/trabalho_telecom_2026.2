"""Testes de limite de tamanho no upload, limite de duração e recuperação ao reiniciar (item 11)."""

import io
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.routing import APIRoute
from starlette.requests import Request

from telecom.accounts.models import Principal, Tenant, User
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UsageRepository, UserRepository
from telecom.web.app import create_app
from telecom.web.jobs import JobService, JobStatus
from tests.test_web_jobs import ImmediateExecutor


class _FakeChunkStream:
    """Simula stream grande para testar aborto imediato acima de 300 MB."""

    def __init__(self, total_bytes: int, chunk_size: int = 1024 * 1024) -> None:
        self.remaining = total_bytes
        self.chunk_size = chunk_size

    def read(self, size: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        n = min(self.remaining, self.chunk_size)
        self.remaining -= n
        return b"X" * n


def _make_request() -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "headers": [(b"host", b"localhost:8000"), (b"origin", b"http://localhost:8000")],
        "path": "/api/v1/sessions",
        "scheme": "http",
        "server": ("localhost", 8000),
    })


def _setup(tmp_path: Path, *, duration_sec: float = 60.0):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    sessions = SessionRepository(db)
    usage = UsageRepository(db)

    users.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=600))
    users.save_user(User("prof-1", "escola-1", "p1@a.com", "Prof 1", "hash", "teacher"))

    service = JobService(
        pipeline_factory=lambda opt, out: None,
        session_repo=sessions,
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
        duration_prober=lambda path: duration_sec,
        user_repo=users,
        usage_repo=usage,
    )
    app = create_app(service, lambda eng: None, db=db)
    route = next(r for r in app.routes if isinstance(r, APIRoute) and r.path == "/api/v1/sessions" and "POST" in r.methods)
    return route, service, sessions, db


def test_oversized_upload_aborts_stream_returns_413_and_deletes_files(tmp_path):
    route, _, _, _ = _setup(tmp_path)
    principal = Principal("escola-1", "prof-1", "teacher")

    # Stream de 350 MB: deve abortar logo após ultrapassar 300 MB, sem ler até o fim
    stream = _FakeChunkStream(total_bytes=350 * 1024 * 1024)
    upload = UploadFile(filename="gigante.mp3", file=stream)

    with pytest.raises(HTTPException) as exc:
        route.endpoint(
            request=_make_request(),
            file=upload,
            consent=True,
            engine="gemini",
            compact_silence=False,
            review=False,
            principal=principal,
        )
    assert exc.value.status_code == 413
    assert "300 MB" in exc.value.detail
    assert stream.remaining > 0, "O upload deveria ter sido abortado antes do fim do stream"

    sessions_dir = tmp_path / "jobs" / "escola-1" / "sessions"
    if sessions_dir.exists():
        assert list(sessions_dir.iterdir()) == []


def test_duration_over_3h_returns_400_and_deletes_files(tmp_path):
    route, _, _, _ = _setup(tmp_path, duration_sec=10801.0)
    principal = Principal("escola-1", "prof-1", "teacher")

    upload = UploadFile(filename="longa.mp3", file=io.BytesIO(b"audio bytes"))
    with pytest.raises(HTTPException) as exc:
        route.endpoint(
            request=_make_request(),
            file=upload,
            consent=True,
            engine="gemini",
            compact_silence=False,
            review=False,
            principal=principal,
        )
    assert exc.value.status_code == 400
    assert "3 horas" in exc.value.detail

    sessions_dir = tmp_path / "jobs" / "escola-1" / "sessions"
    if sessions_dir.exists():
        assert list(sessions_dir.iterdir()) == []


def test_recovery_marks_processing_and_queued_as_failed_on_restart(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    sessions = SessionRepository(db)
    users.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=600))
    users.save_user(User("prof-1", "escola-1", "p1@a.com", "Prof 1", "hash", "teacher"))

    sessions.save("escola-1", {
        "id": "sess-proc", "tenant_id": "escola-1", "teacher_id": "prof-1",
        "file_name": "a.mp3", "status": "processing",
    })
    sessions.save("escola-1", {
        "id": "sess-queue", "tenant_id": "escola-1", "teacher_id": "prof-1",
        "file_name": "b.mp3", "status": "queued",
    })

    # Reinício do serviço: cria nova instância de JobService apontando para o mesmo banco
    restarted = JobService(
        pipeline_factory=lambda opt, out: None,
        session_repo=sessions,
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
    )
    principal = Principal("escola-1", "prof-1", "teacher")

    for sid in ("sess-proc", "sess-queue"):
        job = restarted.get(principal, sid)
        assert job is not None
        assert job.status is JobStatus.FAILED
        assert "servidor reiniciou" in (job.error or "")
