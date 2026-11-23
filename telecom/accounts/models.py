"""Modelos fundamentais de contas e multi-tenancy. Objetos de valor imutáveis."""

from dataclasses import dataclass
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Tenant:
    """Organização cliente (escola de idiomas ou professor autônomo)."""

    id: str
    name: str
    monthly_audio_minutes: int = 300  # Cota mensal em minutos de áudio
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", _utc_now_iso())


@dataclass(frozen=True)
class User:
    """Usuário com acesso ao sistema (owner ou teacher)."""

    id: str
    tenant_id: str
    email: str
    name: str
    password_hash: str
    role: str  # "owner" | "teacher"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", _utc_now_iso())


@dataclass(frozen=True)
class Principal:
    """Contexto autenticado do chamador para autorização e isolamento estrito."""

    tenant_id: str
    user_id: str
    role: str  # "owner" | "teacher"
