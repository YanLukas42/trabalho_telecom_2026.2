"""Repositórios multi-tenant para SQLite.

# shortcut: SQLite em arquivo local sem RLS, isolamento por tenant_id em toda query (TN-03, ADR-0001)
"""

import json
from datetime import datetime, timezone
from typing import Any

from telecom.accounts.models import Tenant, User
from telecom.storage.db import Database


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionRepository:
    """Repositório de sessões de aula (class_sessions)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, tenant_id: str, session_id: str) -> dict[str, Any] | None:
        """Busca sessão exigindo estritamente o tenant_id (TN-03)."""
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM class_sessions WHERE tenant_id = ? AND id = ?",
                (tenant_id, session_id),
            ).fetchone()
            return self._row_to_dict(row) if row else None

    def list(self, tenant_id: str, teacher_id: str | None = None) -> list[dict[str, Any]]:
        """Lista sessões do tenant. Teacher vê apenas as suas; owner vê todas."""
        query = "SELECT * FROM class_sessions WHERE tenant_id = ?"
        params: list[Any] = [tenant_id]
        if teacher_id:
            query += " AND teacher_id = ?"
            params.append(teacher_id)
        query += " ORDER BY created_at DESC"

        with self._db.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def count_active(self, tenant_id: str, teacher_id: str | None = None) -> int:
        """Conta sessões ativas (queued ou processing) do tenant ou do professor."""
        query = "SELECT COUNT(*) as total FROM class_sessions WHERE tenant_id = ? AND status IN ('queued', 'processing')"
        params: list[Any] = [tenant_id]
        if teacher_id:
            query += " AND teacher_id = ?"
            params.append(teacher_id)
        with self._db.connection() as conn:
            row = conn.execute(query, params).fetchone()
            return int(row["total"]) if row else 0

    def save(self, tenant_id: str, data: dict[str, Any]) -> None:
        """Cria ou atualiza uma sessão vinculada ao tenant."""
        opts = data.get("options_json")
        if opts is None and "engine" in data:
            opts = {
                "engine": data.get("engine", "gemini"),
                "compact_silence": bool(data.get("compact_silence", False)),
                "review": bool(data.get("review", False)),
                "original_filename": data.get("original_filename", data.get("filename", "")),
            }
        opts_str = json.dumps(opts) if opts is not None else None
        parts_str = json.dumps(data.get("participants_json")) if data.get("participants_json") is not None else None
        lesson_str = json.dumps(data.get("lesson_json")) if data.get("lesson_json") is not None else None
        file_name = data.get("file_name") or data.get("filename") or ""
        created_at = data.get("created_at") or _utc_now_iso()

        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO class_sessions (
                    id, tenant_id, teacher_id, file_name, status,
                    options_json, error, audio_seconds, created_at,
                    started_at, finished_at, report_json_path, report_md_path,
                    words_json_path, participants_json, lesson_json,
                    consent_at, consent_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    error = excluded.error,
                    audio_seconds = COALESCE(excluded.audio_seconds, class_sessions.audio_seconds),
                    started_at = COALESCE(excluded.started_at, class_sessions.started_at),
                    finished_at = COALESCE(excluded.finished_at, class_sessions.finished_at),
                    report_json_path = COALESCE(excluded.report_json_path, class_sessions.report_json_path),
                    report_md_path = COALESCE(excluded.report_md_path, class_sessions.report_md_path),
                    words_json_path = COALESCE(excluded.words_json_path, class_sessions.words_json_path),
                    participants_json = COALESCE(excluded.participants_json, class_sessions.participants_json),
                    lesson_json = COALESCE(excluded.lesson_json, class_sessions.lesson_json),
                    consent_at = COALESCE(excluded.consent_at, class_sessions.consent_at),
                    consent_version = COALESCE(excluded.consent_version, class_sessions.consent_version);
                """,
                (
                    data["id"],
                    tenant_id,
                    data["teacher_id"],
                    file_name,
                    data["status"],
                    opts_str,
                    data.get("error"),
                    data.get("audio_seconds", 0.0),
                    created_at,
                    data.get("started_at"),
                    data.get("finished_at"),
                    data.get("report_json_path"),
                    data.get("report_md_path"),
                    data.get("words_json_path"),
                    parts_str,
                    lesson_str,
                    data.get("consent_at"),
                    data.get("consent_version"),
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
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE class_sessions
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
        paths: dict[str, str],
        audio_seconds: float = 0.0,
        finished_at: float | None = None,
    ) -> None:
        fin_at = finished_at or datetime.now(timezone.utc).timestamp()
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE class_sessions
                SET status = 'done',
                    report_json_path = ?,
                    report_md_path = ?,
                    words_json_path = ?,
                    audio_seconds = ?,
                    finished_at = ?
                WHERE tenant_id = ? AND id = ?
                """,
                (
                    paths.get("report_json"),
                    paths.get("report_md"),
                    paths.get("words_json"),
                    audio_seconds,
                    fin_at,
                    tenant_id,
                    session_id,
                ),
            )

    def attach_lesson(self, tenant_id: str, session_id: str, lesson_data: dict[str, Any]) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE class_sessions SET lesson_json = ? WHERE tenant_id = ? AND id = ?",
                (json.dumps(lesson_data), tenant_id, session_id),
            )

    def attach_participants(self, tenant_id: str, session_id: str, participants: list[dict[str, Any]]) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "UPDATE class_sessions SET participants_json = ? WHERE tenant_id = ? AND id = ?",
                (json.dumps(participants), tenant_id, session_id),
            )

    def delete(self, tenant_id: str, session_id: str) -> bool:
        with self._db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM class_sessions WHERE tenant_id = ? AND id = ?",
                (tenant_id, session_id),
            )
            return cursor.rowcount > 0

    def recover_active_on_startup(self) -> int:
        with self._db.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE class_sessions
                SET status = 'failed', error = 'servidor reiniciou, envie de novo'
                WHERE status IN ('queued', 'processing')
                """
            )
            return cursor.rowcount

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        opts = json.loads(row["options_json"]) if row["options_json"] else {}
        parts = json.loads(row["participants_json"]) if row["participants_json"] else None
        lesson = json.loads(row["lesson_json"]) if row["lesson_json"] else None
        orig_name = opts.get("original_filename", row["file_name"]) if isinstance(opts, dict) else row["file_name"]
        return {
            "id": row["id"],
            "tenant_id": row["tenant_id"],
            "teacher_id": row["teacher_id"],
            "file_name": row["file_name"],
            "status": row["status"],
            "options_json": opts,
            "error": row["error"],
            "audio_seconds": row["audio_seconds"] or 0.0,
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "report_json_path": row["report_json_path"],
            "report_md_path": row["report_md_path"],
            "words_json_path": row["words_json_path"],
            "participants_json": parts,
            "lesson_json": lesson,
            "consent_at": row["consent_at"],
            "consent_version": row["consent_version"],
            # Campos de conveniência/compatibilidade
            "filename": row["file_name"],
            "original_filename": orig_name,
            "engine": opts.get("engine", "gemini") if isinstance(opts, dict) else "gemini",
            "compact_silence": opts.get("compact_silence", False) if isinstance(opts, dict) else False,
            "review": opts.get("review", False) if isinstance(opts, dict) else False,
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
            return Tenant(id=row["id"], name=row["name"], monthly_audio_minutes=row["monthly_audio_minutes"], created_at=row["created_at"])

    def save_tenant(self, tenant: Tenant) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO tenants (id, name, monthly_audio_minutes, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, monthly_audio_minutes = excluded.monthly_audio_minutes;
                """,
                (tenant.id, tenant.name, tenant.monthly_audio_minutes, tenant.created_at),
            )

    def get_user_by_email(self, email: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()
            if not row:
                return None
            return User(id=row["id"], tenant_id=row["tenant_id"], email=row["email"], name=row["name"], role=row["role"], password_hash=row["password_hash"], created_at=row["created_at"])

    def get_user(self, tenant_id: str, user_id: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE tenant_id = ? AND id = ?", (tenant_id, user_id)).fetchone()
            if not row:
                return None
            return User(id=row["id"], tenant_id=row["tenant_id"], email=row["email"], name=row["name"], role=row["role"], password_hash=row["password_hash"], created_at=row["created_at"])

    def save_user(self, user: User) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, tenant_id, email, name, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET email = excluded.email, name = excluded.name, password_hash = excluded.password_hash, role = excluded.role;
                """,
                (user.id, user.tenant_id, user.email.lower().strip(), user.name, user.password_hash, user.role, user.created_at),
            )


class AuthSessionRepository:
    """Gerencia tokens de sessão persistidos (auth_sessions)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, token_hash: str, user_id: str, tenant_id: str, expires_at: str) -> None:
        with self._db.connection() as conn:
            conn.execute("INSERT INTO auth_sessions (token_hash, user_id, tenant_id, expires_at) VALUES (?, ?, ?, ?)", (token_hash, user_id, tenant_id, expires_at))

    def get(self, token_hash: str) -> dict[str, Any] | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM auth_sessions WHERE token_hash = ?", (token_hash,)).fetchone()
            return dict(row) if row else None

    def delete(self, token_hash: str) -> bool:
        with self._db.connection() as conn:
            cursor = conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,))
            return cursor.rowcount > 0

    def cleanup_expired(self, now_iso: str | None = None) -> int:
        now = now_iso or _utc_now_iso()
        with self._db.connection() as conn:
            cursor = conn.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (now,))
            return cursor.rowcount


class LoginAttemptRepository:
    """Protege contra ataques de força bruta contando tentativas recentes."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def record(self, email: str) -> None:
        with self._db.connection() as conn:
            conn.execute("INSERT INTO login_attempts (email, at) VALUES (?, ?)", (email.lower().strip(), _utc_now_iso()))

    def count_recent(self, email: str, since_iso: str) -> int:
        with self._db.connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM login_attempts WHERE email = ? AND at >= ?", (email.lower().strip(), since_iso)).fetchone()
            return int(row["total"]) if row else 0

    def clear(self, email: str) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM login_attempts WHERE email = ?", (email.lower().strip(),))


class UsageRepository:
    """Registra consumo de áudio e tokens por tenant (TN-14, TN-15)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def record(self, tenant_id: str, session_id: str | None, kind: str, audio_seconds: float, tokens: int) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "INSERT INTO usage_events (tenant_id, session_id, kind, audio_seconds, tokens, at) VALUES (?, ?, ?, ?, ?, ?)",
                (tenant_id, session_id, kind, audio_seconds, tokens, _utc_now_iso()),
            )

    def get_monthly_audio_minutes(self, tenant_id: str, since_iso: str) -> float:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(audio_seconds), 0.0) as total_seconds FROM usage_events WHERE tenant_id = ? AND at >= ? AND kind = 'transcription'",
                (tenant_id, since_iso),
            ).fetchone()
            return float(row["total_seconds"]) / 60.0 if row else 0.0

    def get_total_usage(self, tenant_id: str) -> dict[str, Any]:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(audio_seconds), 0) AS total_seconds, COALESCE(SUM(tokens), 0) AS total_tokens FROM usage_events WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
            return {"total_audio_seconds": float(row["total_seconds"]), "total_tokens": int(row["total_tokens"])}


class AuditRepository:
    """Trilha de auditoria imutável por tenant (SG-11, TN-25)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def record(self, tenant_id: str, actor_id: str, action: str, target: str | None = None) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "INSERT INTO audit_log (tenant_id, actor_id, action, target, at) VALUES (?, ?, ?, ?, ?)",
                (tenant_id, actor_id, action, target, _utc_now_iso()),
            )
