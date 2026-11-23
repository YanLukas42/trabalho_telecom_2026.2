from datetime import datetime, timedelta, timezone
from starlette.requests import Request
from starlette.responses import Response
import pytest
from fastapi import HTTPException

from telecom.accounts.models import Principal, Tenant, User
from telecom.accounts.passwords import hash_password, hash_token
from telecom.storage.db import Database
from telecom.storage.repositories import UsageRepository, UserRepository
from telecom.web.auth import AuthManager, LoginRequest, verify_csrf


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


def test_login_successful_creates_session_and_sets_cookie(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha", monthly_audio_minutes=600))
    users.save_user(User("u-1", "t-1", "ana@alpha.com", "Ana", hash_password("senha-secreta-10"), "owner"))

    auth = AuthManager(db)
    req = make_request("POST", origin="http://localhost:8000")
    resp = Response()

    result = auth.login(req, resp, LoginRequest(email="ana@alpha.com", password="senha-secreta-10"))
    assert result.detail == "Login realizado com sucesso."
    assert result.user["email"] == "ana@alpha.com"
    assert result.user["role"] == "owner"

    cookie_header = resp.headers.get("set-cookie", "")
    assert "pauta_session=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=strict" in cookie_header

    # Token gravado no banco como hash SHA-256
    token = cookie_header.split("pauta_session=")[1].split(";")[0]
    token_hash = hash_token(token)
    session_row = auth.auth_sessions.get(token_hash)
    assert session_row is not None
    assert session_row["user_id"] == "u-1"
    assert session_row["tenant_id"] == "t-1"


def test_login_invalid_credentials_returns_generic_error(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha"))
    users.save_user(User("u-1", "t-1", "ana@alpha.com", "Ana", hash_password("senha-secreta-10"), "teacher"))

    auth = AuthManager(db)
    req = make_request("POST")

    # Senha incorreta
    with pytest.raises(HTTPException) as exc_info:
        auth.login(req, Response(), LoginRequest(email="ana@alpha.com", password="senha-errada-999"))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "E-mail ou senha incorretos."

    # E-mail inexistente
    with pytest.raises(HTTPException) as exc_info:
        auth.login(req, Response(), LoginRequest(email="inexistente@alpha.com", password="senha-secreta-10"))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "E-mail ou senha incorretos."


def test_login_rate_limiting_blocks_after_5_failures(tmp_path):
    db = Database(tmp_path / "test.db")
    auth = AuthManager(db)
    req = make_request("POST")

    # 5 erros consecutivos
    for _ in range(5):
        with pytest.raises(HTTPException) as exc_info:
            auth.login(req, Response(), LoginRequest(email="ataque@alpha.com", password="qualquer-senha"))
        assert exc_info.value.status_code == 401

    # 6ª tentativa bloqueada por rate limit (429)
    with pytest.raises(HTTPException) as exc_info:
        auth.login(req, Response(), LoginRequest(email="ataque@alpha.com", password="qualquer-senha"))
    assert exc_info.value.status_code == 429
    assert "Muitas tentativas" in exc_info.value.detail


def test_login_success_clears_failed_attempts(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha"))
    users.save_user(User("u-1", "t-1", "ana@alpha.com", "Ana", hash_password("senha-secreta-10"), "teacher"))

    auth = AuthManager(db)
    req = make_request("POST")

    # 3 falhas prévias
    for _ in range(3):
        with pytest.raises(HTTPException):
            auth.login(req, Response(), LoginRequest(email="ana@alpha.com", password="errada-senha-10"))

    # Login com sucesso
    auth.login(req, Response(), LoginRequest(email="ana@alpha.com", password="senha-secreta-10"))

    # Contador deve estar zerado
    assert auth.login_attempts.count_recent("ana@alpha.com", "2000-01-01T00:00:00") == 0


def test_logout_deletes_session_and_clears_cookie(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha"))
    users.save_user(User("u-1", "t-1", "ana@alpha.com", "Ana", hash_password("senha-secreta-10"), "owner"))

    auth = AuthManager(db)
    resp = Response()
    auth.login(make_request("POST"), resp, LoginRequest(email="ana@alpha.com", password="senha-secreta-10"))
    token = resp.headers["set-cookie"].split("pauta_session=")[1].split(";")[0]

    logout_req = make_request("POST", cookie=token)
    logout_resp = Response()
    res = auth.logout(logout_req, logout_resp)
    assert res["detail"] == "Desconectado com sucesso."

    # Sessão removida do banco
    assert auth.auth_sessions.get(hash_token(token)) is None


def test_current_principal_dependency(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha"))
    users.save_user(User("u-1", "t-1", "prof@alpha.com", "Prof", hash_password("senha-secreta-10"), "teacher"))

    auth = AuthManager(db)

    # Sem cookie -> 401
    with pytest.raises(HTTPException) as exc:
        auth.current_principal(make_request("GET"))
    assert exc.value.status_code == 401

    # Cookie com sessão válida -> Principal
    resp = Response()
    auth.login(make_request("POST"), resp, LoginRequest(email="prof@alpha.com", password="senha-secreta-10"))
    token = resp.headers["set-cookie"].split("pauta_session=")[1].split(";")[0]

    principal = auth.current_principal(make_request("GET", cookie=token))
    assert principal.tenant_id == "t-1"
    assert principal.user_id == "u-1"
    assert principal.role == "teacher"

    # Sessão expirada -> 401
    expired_token = "expired_secret"
    auth.auth_sessions.save(hash_token(expired_token), "u-1", "t-1", "2020-01-01T00:00:00Z")
    with pytest.raises(HTTPException) as exc:
        auth.current_principal(make_request("GET", cookie=expired_token))
    assert exc.value.status_code == 401
    assert "expirada" in exc.value.detail


def test_me_endpoint_returns_user_and_usage(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola Alpha", monthly_audio_minutes=500))
    users.save_user(User("u-1", "t-1", "ana@alpha.com", "Ana Souza", hash_password("senha-secreta-10"), "owner"))

    usage = UsageRepository(db)
    usage.record("t-1", "sess-1", "transcription", audio_seconds=300.0, tokens=1000)

    auth = AuthManager(db)
    principal = Principal(tenant_id="t-1", user_id="u-1", role="owner")
    me = auth.me(principal)

    assert me.name == "Ana Souza"
    assert me.email == "ana@alpha.com"
    assert me.school == "Escola Alpha"
    assert me.role == "owner"
    assert me.used_minutes_month == 5.0
    assert me.monthly_audio_minutes == 500


def test_csrf_origin_check():
    # POST com Origin cruzado (evil.com) -> 403
    evil_req = make_request("POST", host="localhost:8000", origin="http://evil.com")
    with pytest.raises(HTTPException) as exc:
        verify_csrf(evil_req)
    assert exc.value.status_code == 403
    assert "CSRF" in exc.value.detail

    # POST com Origin legítimo -> OK
    good_req = make_request("POST", host="localhost:8000", origin="http://localhost:8000")
    verify_csrf(good_req)

    # GET não sofre bloqueio de CSRF
    get_req = make_request("GET", host="localhost:8000", origin="http://evil.com")
    verify_csrf(get_req)
