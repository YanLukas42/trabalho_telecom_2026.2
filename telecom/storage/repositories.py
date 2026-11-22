"""Repositórios multi-tenant para sessões, usuários, auditoria e uso.

# shortcut: SQLite em arquivo local sem RLS, isolamento garantido por tenant_id em toda query (TN-03, ADR-0001)
"""

import json
from datetime import datetime, timezone
from typing import Any

from telecom.accounts.models import Tenant, User
from telecom.storage.db import Database


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionRepository:
    """Repositório de sessões de aula (ClassSession / Job)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, tenant_id: str, session_id: str) -> dict[str, Any] | None:
        """Busca sessão exigindo estritamente o tenant_id (TN-03)."""
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE tenant_id = ? AND id = ?",
                (tenant_id, session_id),
            ).fetchone()
            return self._row_to_dict(row) if row else None

    def list(self, tenant_id: str, teacher_id: str | None = None) -> list[dict[str, Any]]:
        """Lista sessões do tenant, opcionalmente filtrando por professor."""
        query = "SELECT * FROM sessions WHERE tenant_id = ?"
        params: list[Any] = [tenant_id]
        if teacher_id:
            query += " AND teacher_id = ?"
            params.append(teacher_id)
        query += " ORDER BY created_at DESC"

        with self._db.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def save(self, tenant_id: str, data: dict[str, Any]) -> None:
        """Cria ou atualiza uma sessão vinculada ao tenant."""
        payload_str = json.dumps(data["payload_json"]) if data.get("payload_json") is not None else None
        lesson_str = json.dumps(data["lesson_json"]) if data.get("lesson_json") is not None else None
        created_at = data.get("created_at") or _utc_now_iso()

        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, tenant_id, teacher_id, filename, original_filename,
                    engine, compact_silence, review, status, error,
                    payload_json, lesson_json, started_at, finished_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    error = excluded.error,
                    payload_json = excluded.payload_json,
                    lesson_json = excluded.lesson_json,
                    started_at = excluded.started_at,
                    finished_at = excluded.finished_at;
                """,
                (
                    data["id"],
                    tenant_id,
                    data["teacher_id"],
                    data["filename"],
                    data["original_filename"],
                    data["engine"],
                    1 if data.get("compact_silence") else 0,
                    1 if data.get("review") else 0,
                    data["status"],
                    data.get("error"),
                    payload_str,
                    lesson_str,
                    data.get("started_at"),
                    data.get("finished_at"),
                    created_at,
                ),
            )

    def update_status(
        self,
        tenant_id: str,
        session_id: str,
        status: str,
        error: str | None = None,
        started_at: float | None = None,
        finished_at: float | None = None,
    ) -> None:
        """Atualiza estado da sessão garantindo que pertença ao tenant."""
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET status = ?, error = ?,
                    started_at = COALESCE(?, started_at),
                    finished_at = COALESCE(?, finished_at)
                WHERE tenant_id = ? AND id = ?
                """,
                (status, error, started_at, finished_at, tenant_id, session_id),
            )

    def attach_results(
        self,
        tenant_id: str,
        session_id: str,
        payload: dict[str, Any],
        finished_at: float,
    ) -> None:
        """Anexa o relatório processado e marca a sessão como concluída."""
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET status = 'done', payload_json = ?, finished_at = ?
                WHERE tenant_id = ? AND id = ?
                """,
                (json.dumps(payload), finished_at, tenant_id, session_id),
            )

    def attach_lesson(
        self,
        tenant_id: str,
        session_id: str,
        lesson_data: dict[str, Any],
    ) -> None:
        """Anexa os materiais pedagógicos da aula (em formato dict/JSON)."""
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE sessions SET lesson_json = ? WHERE tenant_id = ? AND id = ?",
                (json.dumps(lesson_data), tenant_id, session_id),
            )

    def delete(self, tenant_id: str, session_id: str) -> bool:
        """Exclui a sessão se pertencer ao tenant (TN-19)."""
        with self._db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE tenant_id = ? AND id = ?",
                (tenant_id, session_id),
            )
            return cursor.rowcount > 0

    def recover_active_on_startup(self) -> int:
        """Na subida do servidor, marca tarefas não finalizadas como falhas (ADR-0003)."""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET status = 'failed', error = 'servidor reiniciou, envie de novo'
                WHERE status IN ('queued', 'processing')
                """
            )
            return cursor.rowcount

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        payload = json.loads(row["payload_json"]) if row["payload_json"] else None
        lesson = json.loads(row["lesson_json"]) if row["lesson_json"] else None
        return {
            "id": row["id"],
            "tenant_id": row["tenant_id"],
            "teacher_id": row["teacher_id"],
            "filename": row["filename"],
            "original_filename": row["original_filename"],
            "engine": row["engine"],
            "compact_silence": bool(row["compact_silence"]),
            "review": bool(row["review"]),
            "status": row["status"],
            "error": row["error"],
            "payload_json": payload,
            "lesson_json": lesson,
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "created_at": row["created_at"],
        }


class UserRepository:
    """Repositório de organizações e usuários."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
            if not row:
                return None
            return Tenant(
                id=row["id"],
                name=row["name"],
                plan=row["plan"],
                max_audio_seconds=row["max_audio_seconds"],
                max_tokens=row["max_tokens"],
                created_at=row["created_at"],
            )

    def save_tenant(self, tenant: Tenant) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO tenants (id, name, plan, max_audio_seconds, max_tokens, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    plan = excluded.plan,
                    max_audio_seconds = excluded.max_audio_seconds,
                    max_tokens = excluded.max_tokens;
                """,
                (tenant.id, tenant.name, tenant.plan, tenant.max_audio_seconds, tenant.max_tokens, tenant.created_at),
            )

    def get_user_by_email(self, email: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                tenant_id=row["tenant_id"],
                email=row["email"],
                name=row["name"],
                role=row["role"],
                password_hash=row["password_hash"],
                created_at=row["created_at"],
            )

    def get_user(self, tenant_id: str, user_id: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE tenant_id = ? AND id = ?",
                (tenant_id, user_id),
            ).fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                tenant_id=row["tenant_id"],
                email=row["email"],
                name=row["name"],
                role=row["role"],
                password_hash=row["password_hash"],
                created_at=row["created_at"],
            )

    def save_user(self, user: User) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, tenant_id, email, name, role, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    email = excluded.email,
                    name = excluded.name,
                    role = excluded.role,
                    password_hash = excluded.password_hash;
                """,
                (user.id, user.tenant_id, user.email.lower().strip(), user.name, user.role, user.password_hash, user.created_at),
            )


class UsageRepository:
    """Registra e calcula consumo de minutos de áudio e tokens por tenant (TN-14)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def record(
        self,
        tenant_id: str,
        session_id: str | None,
        kind: str,
        audio_seconds: float,
        tokens: int,
    ) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO usage_events (tenant_id, session_id, kind, audio_seconds, tokens, at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tenant_id, session_id, kind, audio_seconds, tokens, _utc_now_iso()),
            )

    def get_total_usage(self, tenant_id: str) -> dict[str, Any]:
        with self._db.connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(audio_seconds), 0) AS total_seconds,
                       COALESCE(SUM(tokens), 0) AS total_tokens
                FROM usage_events WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchone()
            return {
                "total_audio_seconds": float(row["total_seconds"]),
                "total_tokens": int(row["total_tokens"]),
            }


class AuditRepository:
    """Trilha de auditoria imutável de ações por tenant (SG-11, TN-25)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def record(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        target: str | None = None,
    ) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (tenant_id, user_id, action, target, at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, user_id, action, target, _utc_now_iso()),
            )
