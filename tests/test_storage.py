from telecom.accounts.models import Tenant, User
from telecom.storage.db import Database
from telecom.storage.repositories import (
    AuditRepository,
    AuthSessionRepository,
    LoginAttemptRepository,
    SessionRepository,
    UsageRepository,
    UserRepository,
)


def test_database_runs_migrations_and_backup(tmp_path):
    db = Database(tmp_path / "test.db")
    with db.connection() as conn:
        rows = conn.execute("SELECT version FROM schema_version").fetchall()
        assert len(rows) >= 1

    backup_path = tmp_path / "backup.db"
    db.backup(backup_path)
    assert backup_path.is_file()
    backup_db = Database(backup_path)
    with backup_db.connection() as conn:
        b_rows = conn.execute("SELECT version FROM schema_version").fetchall()
        assert len(b_rows) >= 1


def test_user_repository_tenants_and_users(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = UserRepository(db)

    tenant = Tenant(id="t-1", name="Escola Alpha", monthly_audio_minutes=600)
    repo.save_tenant(tenant)
    fetched_tenant = repo.get_tenant("t-1")
    assert fetched_tenant is not None
    assert fetched_tenant.name == "Escola Alpha"
    assert fetched_tenant.monthly_audio_minutes == 600

    user = User(
        id="u-1",
        tenant_id="t-1",
        email="prof@alpha.com",
        name="Professor Rafael",
        password_hash="scrypt$dummy",
        role="teacher",
    )
    repo.save_user(user)

    fetched_user = repo.get_user_by_email("prof@alpha.com")
    assert fetched_user is not None
    assert fetched_user.name == "Professor Rafael"
    assert fetched_user.role == "teacher"

    # Isolamento de usuário por tenant
    assert repo.get_user("t-1", "u-1") is not None
    assert repo.get_user("t-outro", "u-1") is None


def test_session_repository_multi_tenancy(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))
    users.save_tenant(Tenant(id="t-2", name="Escola B"))
    users.save_user(User("prof-1", "t-1", "p1@a.com", "Prof 1", "hash", "teacher"))
    users.save_user(User("prof-2", "t-1", "p2@a.com", "Prof 2", "hash", "teacher"))

    sessions = SessionRepository(db)
    session_data = {
        "id": "sess-1",
        "tenant_id": "t-1",
        "teacher_id": "prof-1",
        "file_name": "aula.mp3",
        "status": "queued",
        "options_json": {"engine": "gemini", "compact_silence": True},
    }
    sessions.save("t-1", session_data)

    # Busca com tenant correto encontra; com tenant errado devolve None (TN-03, TN-04)
    assert sessions.get("t-1", "sess-1") is not None
    assert sessions.get("t-2", "sess-1") is None

    # Listagem por tenant e por professor
    assert len(sessions.list("t-1")) == 1
    assert len(sessions.list("t-1", teacher_id="prof-1")) == 1
    assert len(sessions.list("t-1", teacher_id="prof-2")) == 0
    assert len(sessions.list("t-2")) == 0

    # Atualizações de status e resultados
    sessions.update_status("t-1", "sess-1", "processing")
    assert sessions.get("t-1", "sess-1")["status"] == "processing"

    sessions.attach_results(
        "t-1",
        "sess-1",
        {"report_json": "/tmp/rep.json", "report_md": "/tmp/rep.md", "words_json": "/tmp/w.json"},
        audio_seconds=120.0,
        finished_at=100.0,
    )
    res = sessions.get("t-1", "sess-1")
    assert res["status"] == "done"
    assert res["report_json_path"] == "/tmp/rep.json"
    assert res["audio_seconds"] == 120.0

    # Delete
    assert sessions.delete("t-1", "sess-1") is True
    assert sessions.get("t-1", "sess-1") is None


def test_auth_session_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))
    users.save_user(User("u-1", "t-1", "u1@a.com", "U1", "hash", "teacher"))

    auth_sessions = AuthSessionRepository(db)
    auth_sessions.save("hash123", "u-1", "t-1", "2099-01-01T00:00:00Z")

    sess = auth_sessions.get("hash123")
    assert sess is not None
    assert sess["user_id"] == "u-1"
    assert sess["tenant_id"] == "t-1"

    # Delete
    assert auth_sessions.delete("hash123") is True
    assert auth_sessions.get("hash123") is None

    # Cleanup expired
    auth_sessions.save("expired_hash", "u-1", "t-1", "2020-01-01T00:00:00Z")
    cleaned = auth_sessions.cleanup_expired("2021-01-01T00:00:00Z")
    assert cleaned == 1
    assert auth_sessions.get("expired_hash") is None


def test_login_attempt_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    login_attempts = LoginAttemptRepository(db)

    login_attempts.record("prof@escola.com")
    login_attempts.record("prof@escola.com")
    assert login_attempts.count_recent("prof@escola.com", "2000-01-01T00:00:00") == 2
    assert login_attempts.count_recent("outro@escola.com", "2000-01-01T00:00:00") == 0

    login_attempts.clear("prof@escola.com")
    assert login_attempts.count_recent("prof@escola.com", "2000-01-01T00:00:00") == 0


def test_usage_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))

    usage = UsageRepository(db)
    usage.record("t-1", "sess-1", "transcription", audio_seconds=120.0, tokens=3500)
    usage.record("t-1", "sess-1", "lesson", audio_seconds=0.0, tokens=1500)

    total = usage.get_total_usage("t-1")
    assert total["total_audio_seconds"] == 120.0
    assert total["total_tokens"] == 5000

    monthly = usage.get_monthly_audio_minutes("t-1", "2000-01-01T00:00:00")
    assert monthly == 2.0


def test_audit_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))
    users.save_user(User("u-1", "t-1", "a@a.com", "A", "hash", "owner"))

    audit = AuditRepository(db)
    audit.record("t-1", "u-1", "class_session.delete", target="sess-99")
    with db.connection() as conn:
        row = conn.execute("SELECT * FROM audit_log WHERE tenant_id = ?", ("t-1",)).fetchone()
        assert row["action"] == "class_session.delete"
        assert row["target"] == "sess-99"
        assert row["actor_id"] == "u-1"
