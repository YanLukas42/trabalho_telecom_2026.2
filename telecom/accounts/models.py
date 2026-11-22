"""Modelos fundamentais de contas e multi-tenancy. Objetos de valor imutáveis."""

from dataclasses import dataclass
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Tenant:
    """Organização cliente (escola, curso ou professor autônomo)."""

    id: str
    name: str
    plan: str = "standard"
    max_audio_seconds: int = 3600 * 5  # shortcut: 5 horas por padrão no MVP, trocar por planos em tabela
    max_tokens: int = 1_000_000
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", _utc_now_iso())


@dataclass(frozen=True)
class User:
    """Usuário autenticado vinculado a um tenant."""

    id: str
    tenant_id: str
    email: str
    name: str
    role: str  # "owner", "teacher", "coordinator"
    password_hash: str
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", _utc_now_iso())


@dataclass(frozen=True)
class Principal:
    """Contexto do chamador autenticado para autorização e isolamento estrito."""

    tenant_id: str
    user_id: str
    role: str  # "owner", "teacher", "coordinator"
