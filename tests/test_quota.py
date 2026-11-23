"""Testes de cota mensal e limite de aulas ativas na rota POST /api/v1/sessions (item 11)."""

import io
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.routing import APIRoute
from starlette.requests import Request

from telecom.accounts.models import Principal, Tenant, User
from telecom.diarization.pipeline import DiarizationOutputs
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UsageRepository, UserRepository
from telecom.web.app import create_app
from telecom.web.jobs import JobService
from tests.test_web_jobs import ImmediateExecutor


class _FakePipeline:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def run(self, source: Path) -> DiarizationOutputs:
        reports = self.output_dir / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        rep = reports / f"{source.stem}.json"
        rep.write_text('{"segmentos": []}', encoding="utf-8")
        return DiarizationOutputs(
            payload={"duracao_original_segundos": 60.0, "metricas_tokens": {"total_tokens": 100}, "segmentos": []},
            report_json=rep,
            report_md=reports / f"{source.stem}.md",
            words_json=reports / f"{source.stem}_w.json",
            words=None,
        )


def _find_post_sessions(app) -> APIRoute:
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == "/api/v1/sessions" and "POST" in r.methods:
            return r
    raise AssertionError("Rota POST /api/v1/sessions não encontrada")


def _make_request() -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "headers": [(b"host", b"localhost:8000"), (b"origin", b"http://localhost:8000")],
        "path": "/api/v1/sessions",
        "scheme": "http",
        "server": ("localhost", 8000),
    })


def _setup(tmp_path: Path, *, monthly_minutes: int = 60, duration_sec: float = 60.0):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    sessions = SessionRepository(db)
    usage = UsageRepository(db)

    users.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=monthly_minutes))
    users.save_user(User("prof-1", "escola-1", "p1@a.com", "Prof 1", "hash", "teacher"))
    users.save_user(User("prof-2", "escola-1", "p2@a.com", "Prof 2", "hash", "teacher"))
    users.save_user(User("prof-3", "escola-1", "p3@a.com", "Prof 3", "hash", "teacher"))

    service = JobService(
        pipeline_factory=lambda opt, out: _FakePipeline(out),
        session_repo=sessions,
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
        duration_prober=lambda path: duration_sec,
        user_repo=users,
        usage_repo=usage,
    )
    app = create_app(service, lambda eng: None, db=db)
    return _find_post_sessions(app), sessions, usage


def test_quota_exceeded_returns_429_via_route(tmp_path):
    route, _, usage = _setup(tmp_path, monthly_minutes=60, duration_sec=900.0)
    principal = Principal("escola-1", "prof-1", "teacher")

    # 50 min usados no mês atual + 15 min desta aula > 60 min
    usage.record("escola-1", "sess-antiga", "transcription", audio_seconds=3000.0, tokens=200)

    upload = UploadFile(filename="aula.mp3", file=io.BytesIO(b"fake audio"))
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
    assert exc.value.status_code == 429
    assert "Sua escola usou 50 de 60 minutos este mês." in exc.value.detail
    assert "Renova em 01/" in exc.value.detail


def test_active_session_limits_return_429_via_route(tmp_path):
    route, sessions, _ = _setup(tmp_path, monthly_minutes=600, duration_sec=60.0)
    prof1 = Principal("escola-1", "prof-1", "teacher")
    prof3 = Principal("escola-1", "prof-3", "teacher")

    sessions.save("escola-1", {
        "id": "ativa-1", "tenant_id": "escola-1", "teacher_id": "prof-1",
        "file_name": "a.mp3", "status": "processing",
    })

    # Professor 1 já tem 1 aula ativa -> 429
    with pytest.raises(HTTPException) as exc_prof:
        route.endpoint(
            request=_make_request(),
            file=UploadFile(filename="b.mp3", file=io.BytesIO(b"audio")),
            consent=True,
            engine="gemini",
            compact_silence=False,
            review=False,
            principal=prof1,
        )
    assert exc_prof.value.status_code == 429
    assert "Espere a aula anterior terminar." in exc_prof.value.detail

    # Escola passa a ter 2 aulas ativas -> Professor 3 recebe 429
    sessions.save("escola-1", {
        "id": "ativa-2", "tenant_id": "escola-1", "teacher_id": "prof-2",
        "file_name": "c.mp3", "status": "queued",
    })
    with pytest.raises(HTTPException) as exc_school:
        route.endpoint(
            request=_make_request(),
            file=UploadFile(filename="d.mp3", file=io.BytesIO(b"audio")),
            consent=True,
            engine="gemini",
            compact_silence=False,
            review=False,
            principal=prof3,
        )
    assert exc_school.value.status_code == 429
    assert "Espere a aula anterior terminar." in exc_school.value.detail
