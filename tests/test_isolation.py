"""Teste automático de isolamento entre escolas e professores em TODAS as rotas de app.routes (item 11).

Percorre app.routes dinamicamente: qualquer rota nova com {session_id} entra neste teste automaticamente.
"""

import inspect
import io
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from telecom.accounts.models import Tenant, User
from telecom.accounts.passwords import hash_password
from telecom.diarization.pipeline import DiarizationOutputs
from telecom.lessons.materials import LessonMaterials, validated_materials
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UserRepository
from telecom.web.app import create_app
from telecom.web.auth import AuthManager, LoginRequest
from telecom.web.jobs import JobOptions, JobService
from telecom.web.schemas import LessonRequestBody, ParticipantBody
from tests.test_web_jobs import ImmediateExecutor


class _FakePipeline:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def run(self, source: Path) -> DiarizationOutputs:
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        rep_json = reports_dir / f"{source.stem}_diarizacao_pydantic.json"
        rep_md = reports_dir / f"{source.stem}_diarizacao_pydantic.md"
        w_json = reports_dir / f"{source.stem}_palavra_por_palavra.json"
        rep_json.write_text(
            '{"segmentos": [{"quemfala": "Aluno", "textodefala": "I go yesterday", "segundos_inicio": 0, "segundos_fim": 1}]}',
            encoding="utf-8",
        )
        rep_md.write_text("# Transcrição", encoding="utf-8")
        w_json.write_text('{"total_palavras": 3}', encoding="utf-8")
        return DiarizationOutputs(
            payload={
                "duracao_original_segundos": 60.0,
                "metricas_tokens": {"total_tokens": 100},
                "segmentos": [{"quemfala": "Aluno", "textodefala": "I go yesterday", "segundos_inicio": 0, "segundos_fim": 1}],
            },
            report_json=rep_json,
            report_md=rep_md,
            words_json=w_json,
            words=None,
        )


class _FakeLessonWriter:
    last_tokens = 250

    def write(self, segments, request):
        return validated_materials(
            LessonMaterials.model_validate(_VALID_LESSON_DICT),
            request,
            segments,
        )


_VALID_LESSON_DICT: dict[str, Any] = {
    "students": [{
        "speaker": "Aluno",
        "strength": "Fala bem.",
        "mistakes": [{"quote": "I go yesterday", "correction": "I went yesterday", "explanation": "Passado simples."}],
        "exercises": [{"kind": "short_answer", "prompt": "Complete.", "options": [], "answer": "went"}],
    }],
    "plan": {"objective": "Passado simples", "topics": ["Verbos"], "blocks": [], "homework": "Ex 1"},
}


def _make_request(method: str, path: str, cookie: str | None = None) -> Request:
    headers = [(b"host", b"localhost:8000"), (b"origin", b"http://localhost:8000")]
    if cookie:
        headers.append((b"cookie", f"pauta_session={cookie}".encode()))
    return Request({
        "type": "http",
        "method": method,
        "headers": headers,
        "path": path,
        "scheme": "http",
        "server": ("localhost", 8000),
    })


def _login_cookie(auth: AuthManager, email: str) -> str:
    resp = Response()
    auth.login(_make_request("POST", "/api/v1/auth/login"), resp, LoginRequest(email=email, password="senha-segura-123"))
    return resp.headers["set-cookie"].split("pauta_session=")[1].split(";")[0]


def _invoke_route(route: APIRoute, method: str, *, cookie: str, session_id: str) -> int:
    req = _make_request(method, route.path.replace("{session_id}", session_id), cookie=cookie)
    try:
        principal = None
        for dep in route.dependant.dependencies:
            if dep.call and dep.call.__name__ == "current_principal":
                principal = dep.call(req)

        kwargs: dict[str, Any] = {}
        sig = inspect.signature(route.endpoint)
        for name in sig.parameters:
            if name == "request":
                kwargs["request"] = req
            elif name == "session_id":
                kwargs["session_id"] = session_id
            elif name == "kind":
                kwargs["kind"] = "md"
            elif name == "principal":
                kwargs["principal"] = principal
            elif name == "participants":
                kwargs["participants"] = [ParticipantBody(label="Aluno", name="Ana", role="student")]
            elif name == "body":
                if method == "POST":
                    kwargs["body"] = LessonRequestBody(
                        level="B1",
                        participants=[ParticipantBody(label="Aluno", name="Ana", role="student")],
                        exercises_per_student=3,
                    )
                else:
                    kwargs["body"] = _VALID_LESSON_DICT

        result = route.endpoint(**kwargs)
        if isinstance(result, FileResponse):
            return result.status_code
        return route.status_code or 200
    except HTTPException as exc:
        return exc.status_code


@pytest.fixture
def env(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="escola-a", name="Escola A", monthly_audio_minutes=600))
    users.save_tenant(Tenant(id="escola-b", name="Escola B", monthly_audio_minutes=600))

    pw = hash_password("senha-segura-123")
    users.save_user(User("prof-a1", "escola-a", "a1@a.com", "Prof A1", pw, "teacher"))
    users.save_user(User("prof-a2", "escola-a", "a2@a.com", "Prof A2", pw, "teacher"))
    users.save_user(User("owner-a", "escola-a", "owner@a.com", "Owner A", pw, "owner"))
    users.save_user(User("prof-b1", "escola-b", "b1@b.com", "Prof B1", pw, "teacher"))
    users.save_user(User("owner-b", "escola-b", "owner@b.com", "Owner B", pw, "owner"))

    repo = SessionRepository(db)
    service = JobService(
        pipeline_factory=lambda opt, out: _FakePipeline(out),
        session_repo=repo,
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
    )
    app = create_app(service, lambda eng: None, lambda: _FakeLessonWriter(), db=db)
    auth = AuthManager(db)

    cookies = {
        "prof_a1": _login_cookie(auth, "a1@a.com"),
        "prof_a2": _login_cookie(auth, "a2@a.com"),
        "owner_a": _login_cookie(auth, "owner@a.com"),
        "prof_b1": _login_cookie(auth, "b1@b.com"),
        "owner_b": _login_cookie(auth, "owner@b.com"),
    }
    return app, service, auth, cookies


def test_all_protected_v1_routes_require_principal(env):
    app, _, _, _ = env
    public = {"/api/v1/auth/login", "/api/v1/auth/logout"}
    v1_routes = [r for r in app.routes if isinstance(r, APIRoute) and r.path.startswith("/api/v1/")]
    assert len(v1_routes) >= 11

    for route in v1_routes:
        if route.path in public:
            continue
        deps = [d.call.__name__ for d in route.dependant.dependencies if d.call]
        assert "current_principal" in deps, f"Rota {route.methods} {route.path} não exige current_principal"


def test_every_session_route_enforces_tenant_and_teacher_isolation(env):
    """Para cada rota com {session_id} em app.routes:
    - Escola B (professor ou owner) -> sempre 404
    - Professor B da Escola A -> sempre 404
    - Owner da Escola A -> 200
    """
    app, service, auth, cookies = env
    principal_a1 = auth.current_principal(_make_request("GET", "/", cookie=cookies["prof_a1"]))

    session_routes: list[tuple[APIRoute, str]] = [
        (r, m)
        for r in app.routes
        if isinstance(r, APIRoute) and "{session_id}" in r.path
        for m in sorted(r.methods)
    ]
    assert len(session_routes) >= 7

    for route, method in session_routes:
        job = service.submit(principal_a1, "aula.mp3", io.BytesIO(b"fake audio bytes"), JobOptions(), consent=True)

        assert _invoke_route(route, method, cookie=cookies["prof_b1"], session_id=job.id) == 404, (
            f"Vazamento entre escolas (prof_b1) em {method} {route.path}"
        )
        assert _invoke_route(route, method, cookie=cookies["owner_b"], session_id=job.id) == 404, (
            f"Vazamento entre escolas (owner_b) em {method} {route.path}"
        )
        assert _invoke_route(route, method, cookie=cookies["prof_a2"], session_id=job.id) == 404, (
            f"Vazamento entre professores da mesma escola (prof_a2) em {method} {route.path}"
        )
        assert _invoke_route(route, method, cookie=cookies["owner_a"], session_id=job.id) == 200, (
            f"Owner da escola A não conseguiu acessar {method} {route.path}"
        )
