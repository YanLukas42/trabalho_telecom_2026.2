"""Pacote de persistência em SQLite.

# shortcut: SQLite em arquivo local sem RLS, trocar por Postgres+RLS com mais de 1 servidor ou ~50 escolas (ADR-0001)
"""

from telecom.storage.db import Database
from telecom.storage.repositories import (
    AuditRepository,
    SessionRepository,
    UsageRepository,
    UserRepository,
)

__all__ = [
    "AuditRepository",
    "Database",
    "SessionRepository",
    "UsageRepository",
    "UserRepository",
]
