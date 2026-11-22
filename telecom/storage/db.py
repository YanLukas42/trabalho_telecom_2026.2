"""Camada de acesso a dados SQLite. Único módulo autorizado a importar sqlite3.

# shortcut: SQLite em arquivo local sem RLS, trocar por Postgres+RLS com mais de 1 servidor ou ~50 escolas (ADR-0001)
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Sequence

MIGRATIONS: Sequence[str] = (
    # V1: Tabelas essenciais do MVP multi-tenant
    """
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        plan TEXT NOT NULL,
        max_audio_seconds INTEGER NOT NULL DEFAULT 18000,
        max_tokens INTEGER NOT NULL DEFAULT 1000000,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        email TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        teacher_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        engine TEXT NOT NULL,
        compact_silence INTEGER NOT NULL DEFAULT 0,
        review INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        error TEXT,
        payload_json TEXT,
        lesson_json TEXT,
        started_at REAL,
        finished_at REAL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_teacher ON sessions(tenant_id, teacher_id);

    CREATE TABLE IF NOT EXISTS usage_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        session_id TEXT,
        kind TEXT NOT NULL,
        audio_seconds REAL NOT NULL DEFAULT 0.0,
        tokens INTEGER NOT NULL DEFAULT 0,
        at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_events(tenant_id);

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        target TEXT,
        at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id);
    """,
)


class Database:
    """Gerencia conexões e migrações do banco SQLite."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Abre uma conexão com WAL e foreign keys ativas, e comita ao fechar."""
        conn = sqlite3.connect(str(self.path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Executa migrações pendentes em ordem."""
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                """
            )
            applied_rows = conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
            applied_versions = {row["version"] for row in applied_rows}

            for idx, sql_script in enumerate(MIGRATIONS, start=1):
                if idx not in applied_versions:
                    conn.executescript(sql_script)
                    now_iso = datetime.now(timezone.utc).isoformat()
                    conn.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                        (idx, now_iso),
                    )
