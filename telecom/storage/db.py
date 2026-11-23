"""Camada de banco SQLite. Único módulo que importa sqlite3.

# shortcut: SQLite em arquivo local sem RLS, isolamento no repositório (ADR-0001)
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Sequence

MIGRATIONS: Sequence[str] = (
    # V1: Esquema multi-tenant do MVP
    """
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        monthly_audio_minutes INTEGER NOT NULL DEFAULT 300,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        email TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);

    CREATE TABLE IF NOT EXISTS auth_sessions (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        expires_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_auth_sessions_tenant ON auth_sessions(tenant_id, user_id);

    CREATE TABLE IF NOT EXISTS class_sessions (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        teacher_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        file_name TEXT NOT NULL,
        status TEXT NOT NULL,
        options_json TEXT,
        error TEXT,
        audio_seconds REAL DEFAULT 0.0,
        created_at TEXT NOT NULL,
        started_at REAL,
        finished_at REAL,
        report_json_path TEXT,
        report_md_path TEXT,
        words_json_path TEXT,
        participants_json TEXT,
        lesson_json TEXT,
        consent_at TEXT,
        consent_version TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_class_sessions_tenant ON class_sessions(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_class_sessions_tenant_teacher ON class_sessions(tenant_id, teacher_id);

    CREATE TABLE IF NOT EXISTS usage_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        session_id TEXT,
        kind TEXT NOT NULL,
        audio_seconds REAL NOT NULL DEFAULT 0.0,
        tokens INTEGER NOT NULL DEFAULT 0,
        at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_usage_events_tenant ON usage_events(tenant_id);

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL,
        target TEXT,
        at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON audit_log(tenant_id);

    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email, at);
    """,
)


class Database:
    """Gerencia conexões, migrações e backup do banco SQLite."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Abre conexão com WAL e foreign keys ativas, comitando ao sair."""
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

    def backup(self, destination_path: Path | str) -> None:
        """Realiza backup online atômico do banco SQLite usando a API nativa."""
        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as src_conn:
            dest_conn = sqlite3.connect(str(dest))
            try:
                src_conn.backup(dest_conn)
            finally:
                dest_conn.close()

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
