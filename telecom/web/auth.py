"""Serviço e rotas de autenticação, sessões e proteção CSRF.

# shortcut: sessão via cookie de 12h com hash SHA-256 no SQLite, trocar por OIDC no cadastro aberto (ADR-0002)
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, EmailStr

from telecom.accounts.models import Principal, User
from telecom.accounts.passwords import hash_token, verify_password
from telecom.settings import PAUTA_COOKIE_SECURE, SESSION_COOKIE_NAME, SESSION_DURATION_HOURS
from telecom.storage.db import Database
from telecom.storage.repositories import (
    AuditRepository,
    AuthSessionRepository,
    LoginAttemptRepository,
    UsageRepository,
    UserRepository,
)

LOGIN_MAX_ATTEMPTS = 5
LOGIN_ATTEMPTS_WINDOW_MINUTES = 15
LOGIN_ERROR_MESSAGE = "E-mail ou senha incorretos."


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    detail: str
    user: dict[str, Any]


class MeResponse(BaseModel):
    name: str
    email: str
    school: str
    role: str
    used_minutes_month: float
    monthly_audio_minutes: int
    # Aliases de compatibilidade para interface
    nome: str
    escola: str
    papel: str
    uso_mes: float
    limite_mes: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def verify_csrf(request: Request) -> None:
    """Verifica se o cabeçalho Origin corresponde ao próprio site em mutações (CSRF)."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        origin = request.headers.get("origin")
        if origin:
            parsed = urlparse(origin)
            req_host = (request.headers.get("host") or "").lower()
            base_netloc = request.base_url.netloc.lower()
            origin_netloc = parsed.netloc.lower()
            if origin_netloc != req_host and origin_netloc != base_netloc:
                raise HTTPException(status_code=403, detail="Origem não permitida (CSRF).")


class AuthManager:
    """Centraliza a lógica de autenticação, sessões e controle de tentativas."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.auth_sessions = AuthSessionRepository(db)
        self.login_attempts = LoginAttemptRepository(db)
        self.usage = UsageRepository(db)
        self.audit = AuditRepository(db)

    def login(self, request: Request, response: Response, body: LoginRequest) -> LoginResponse:
        verify_csrf(request)
        email = body.email.lower().strip()

        # Limite de tentativas contra força bruta (5 erros / 15 min -> 429)
        since = (_utc_now() - timedelta(minutes=LOGIN_ATTEMPTS_WINDOW_MINUTES)).isoformat()
        if self.login_attempts.count_recent(email, since) >= LOGIN_MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Muitas tentativas de login. Tente novamente em 15 minutos.")

        user = self.users.get_user_by_email(email)
        if not user or not verify_password(body.password, user.password_hash):
            self.login_attempts.record(email)
            raise HTTPException(status_code=401, detail=LOGIN_ERROR_MESSAGE)

        self.login_attempts.clear(email)

        token = secrets.token_urlsafe(32)
        token_hash = hash_token(token)
        expires_at = (_utc_now() + timedelta(hours=SESSION_DURATION_HOURS)).isoformat()
        self.auth_sessions.save(token_hash, user.id, user.tenant_id, expires_at)

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            max_age=SESSION_DURATION_HOURS * 3600,
            httponly=True,
            samesite="strict",
            secure=PAUTA_COOKIE_SECURE,
            path="/",
        )

        return LoginResponse(
            detail="Login realizado com sucesso.",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "tenant_id": user.tenant_id,
            },
        )

    def logout(self, request: Request, response: Response) -> dict[str, str]:
        verify_csrf(request)
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            self.auth_sessions.delete(hash_token(token))

        response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
        return {"detail": "Desconectado com sucesso."}

    def me(self, principal: Principal) -> MeResponse:
        user = self.users.get_user(principal.tenant_id, principal.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        tenant = self.users.get_tenant(principal.tenant_id)
        school_name = tenant.name if tenant else ""
        monthly_limit = tenant.monthly_audio_minutes if tenant else 0

        now = _utc_now()
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()
        used_minutes = self.usage.get_monthly_audio_minutes(principal.tenant_id, month_start)
        rounded_used = round(used_minutes, 2)

        return MeResponse(
            name=user.name,
            email=user.email,
            school=school_name,
            role=principal.role,
            used_minutes_month=rounded_used,
            monthly_audio_minutes=monthly_limit,
            nome=user.name,
            escola=school_name,
            papel=principal.role,
            uso_mes=rounded_used,
            limite_mes=monthly_limit,
        )

    def current_principal(self, request: Request) -> Principal:
        """Extrai o Principal autenticado do cookie pauta_session."""
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            raise HTTPException(status_code=401, detail="Não autenticado.")

        token_hash = hash_token(token)
        sess = self.auth_sessions.get(token_hash)
        if not sess:
            raise HTTPException(status_code=401, detail="Não autenticado.")

        if sess["expires_at"] < _utc_now().isoformat():
            self.auth_sessions.delete(token_hash)
            raise HTTPException(status_code=401, detail="Sessão expirada.")

        user = self.users.get_user(sess["tenant_id"], sess["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado.")

        return Principal(tenant_id=sess["tenant_id"], user_id=sess["user_id"], role=user.role)
