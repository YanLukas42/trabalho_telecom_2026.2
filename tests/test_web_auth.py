"""Testes das rotas web de autenticação, cookies e exigência de sessão em todas as rotas (item 11)."""

from fastapi import HTTPException
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
import pytest

from telecom.accounts.models import Tenant, User
from telecom.accounts.passwords import hash_password, hash_token
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UserRepository
from telecom.web.app import create_app
from telecom.web.auth import LoginRequest
from telecom.web.jobs import JobService
from tests.test_web_jobs import ImmediateExecutor


def _make_request(method: str = "GET", path: str = "/", host: str = "localhost:8000", origin: str | None = None, cookie: str | None = None) -> Request:
    headers = [(b"host", host.encode())]
    if origin:
        headers.append((b"origin", origin.encode()))
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


def _find_route(app, method: str, path: str) -> APIRoute:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"Rota {method} {path} não encontrada em app.routes")


def _build_app(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="escola-1", name="Escola Alpha", monthly_audio_minutes=600))
    users.save_user(User(
        id="u-1",
        tenant_id="escola-1",
        email="ana@alpha.com",
        name="Ana",
        password_hash=hash_password("senha-forte-123"),
        role="owner",
    ))
    service = JobService(
        pipeline_factory=lambda opt, out: None,
        session_repo=SessionRepository(db),
        base_dir=tmp_path / "jobs",
        executor=ImmediateExecutor(),
    )
    app = create_app(service, lambda eng: None, db=db)
    return app, db


def test_web_login_sets_cookie_flags_and_persists_sha256(tmp_path, monkeypatch):
    app, db = _build_app(tmp_path)
    login_route = _find_route(app, "POST", "/api/v1/auth/login")
    me_route = _find_route(app, "GET", "/api/v1/me")

    # Ambiente localhost: PAUTA_COOKIE_SECURE=0 -> HttpOnly, SameSite=strict, sem flag Secure
    monkeypatch.setattr("telecom.web.auth.PAUTA_COOKIE_SECURE", False)
    req = _make_request("POST", "/api/v1/auth/login", origin="http://localhost:8000")
    resp = Response()
    res = login_route.endpoint(req, resp, LoginRequest(email="ana@alpha.com", password="senha-forte-123"))
    assert res.user["email"] == "ana@alpha.com"

    cookie_hdr = resp.headers["set-cookie"]
    assert "pauta_session=" in cookie_hdr
    assert "HttpOnly" in cookie_hdr
    assert "SameSite=strict" in cookie_hdr
    assert "; Secure" not in cookie_hdr

    token = cookie_hdr.split("pauta_session=")[1].split(";")[0]
    with db.connection() as conn:
        row = conn.execute("SELECT token_hash FROM auth_sessions WHERE token_hash = ?", (hash_token(token),)).fetchone()
        assert row is not None

    # Confirma que a dependência de /me aceita o cookie emitido
    principal_dep = me_route.dependant.dependencies[0].call
    principal = principal_dep(_make_request("GET", "/api/v1/me", cookie=token))
    assert principal.tenant_id == "escola-1"
    assert principal.user_id == "u-1"

    # Produção (PAUTA_COOKIE_SECURE=1): cookie precisa incluir Secure
    monkeypatch.setattr("telecom.web.auth.PAUTA_COOKIE_SECURE", True)
    resp_prod = Response()
    login_route.endpoint(_make_request("POST", "/api/v1/auth/login", origin="http://localhost:8000"), resp_prod, LoginRequest(email="ana@alpha.com", password="senha-forte-123"))
    assert "Secure" in resp_prod.headers["set-cookie"]


def test_web_login_wrong_credentials_and_logout_invalidates_cookie(tmp_path):
    app, _ = _build_app(tmp_path)
    login_route = _find_route(app, "POST", "/api/v1/auth/login")
    logout_route = _find_route(app, "POST", "/api/v1/auth/logout")
    me_route = _find_route(app, "GET", "/api/v1/me")
    principal_dep = me_route.dependant.dependencies[0].call

    # Senha errada e e-mail inexistente devolvem exatamente a mesma mensagem e código 401
    with pytest.raises(HTTPException) as exc_pw:
        login_route.endpoint(_make_request("POST"), Response(), LoginRequest(email="ana@alpha.com", password="errada-password"))
    with pytest.raises(HTTPException) as exc_email:
        login_route.endpoint(_make_request("POST"), Response(), LoginRequest(email="naoexiste@alpha.com", password="senha-forte-123"))
    assert exc_pw.value.status_code == 401
    assert exc_email.value.status_code == 401
    assert exc_pw.value.detail == exc_email.value.detail == "E-mail ou senha incorretos."

    # Login válido -> Logout -> chamada subsequente com o mesmo cookie devolve 401
    resp_login = Response()
    login_route.endpoint(_make_request("POST", origin="http://localhost:8000"), resp_login, LoginRequest(email="ana@alpha.com", password="senha-forte-123"))
    token = resp_login.headers["set-cookie"].split("pauta_session=")[1].split(";")[0]

    resp_logout = Response()
    logout_route.endpoint(_make_request("POST", "/api/v1/auth/logout", origin="http://localhost:8000", cookie=token), resp_logout)
    assert "Max-Age=0" in resp_logout.headers["set-cookie"] or "expires=" in resp_logout.headers["set-cookie"].lower()

    with pytest.raises(HTTPException) as exc_after:
        principal_dep(_make_request("GET", "/api/v1/me", cookie=token))
    assert exc_after.value.status_code == 401


def test_every_protected_v1_route_returns_401_without_login(tmp_path):
    """Varre todas as rotas /api/v1/* em app.routes e confirma que sem cookie todas respondem 401."""
    app, _ = _build_app(tmp_path)
    public_routes = {"/api/v1/auth/login", "/api/v1/auth/logout"}
    protected = [
        r for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/v1/") and r.path not in public_routes
    ]
    assert len(protected) >= 10

    for route in protected:
        principal_deps = [d.call for d in route.dependant.dependencies if d.call and d.call.__name__ == "current_principal"]
        assert principal_deps, f"Rota {route.methods} {route.path} está sem dependência current_principal"
        req = _make_request(next(iter(route.methods)), route.path)
        with pytest.raises(HTTPException) as exc:
            principal_deps[0](req)
        assert exc.value.status_code == 401, f"Rota {route.methods} {route.path} não respondeu 401 sem cookie"


def test_web_login_rate_limiting_after_5_failures(tmp_path):
    app, _ = _build_app(tmp_path)
    login_route = _find_route(app, "POST", "/api/v1/auth/login")

    for _ in range(5):
        with pytest.raises(HTTPException) as exc:
            login_route.endpoint(_make_request("POST"), Response(), LoginRequest(email="ana@alpha.com", password="errada-password"))
        assert exc.value.status_code == 401

    with pytest.raises(HTTPException) as exc_blocked:
        login_route.endpoint(_make_request("POST"), Response(), LoginRequest(email="ana@alpha.com", password="senha-forte-123"))
    assert exc_blocked.value.status_code == 429
