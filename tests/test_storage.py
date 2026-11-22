from telecom.accounts.models import Tenant, User
from telecom.storage.db import Database
from telecom.storage.repositories import (
    AuditRepository,
    SessionRepository,
    UsageRepository,
    UserRepository,
)


def test_database_runs_migrations(tmp_path):
    db = Database(tmp_path / "test.db")
    with db.connection() as conn:
        rows = conn.execute("SELECT version FROM schema_version").fetchall()
        assert len(rows) >= 1


def test_user_repository_tenants_and_users(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = UserRepository(db)

    tenant = Tenant(id="t-1", name="Escola Alpha")
    repo.save_tenant(tenant)
    fetched_tenant = repo.get_tenant("t-1")
    assert fetched_tenant is not None
    assert fetched_tenant.name == "Escola Alpha"

    user = User(
        id="u-1",
        tenant_id="t-1",
        email="prof@alpha.com",
        name="Professor Rafael",
        role="teacher",
        password_hash="scrypt$dummy",
    )
    repo.save_user(user)

    fetched_user = repo.get_user_by_email("prof@alpha.com")
    assert fetched_user is not None
    assert fetched_user.name == "Professor Rafael"

    # Isolamento de usuário por tenant
    assert repo.get_user("t-1", "u-1") is not None
    assert repo.get_user("t-outro", "u-1") is None


def test_session_repository_multi_tenancy(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))
    users.save_tenant(Tenant(id="t-2", name="Escola B"))

    sessions = SessionRepository(db)
    session_data = {
        "id": "sess-1",
        "tenant_id": "t-1",
        "teacher_id": "prof-1",
        "filename": "aula.mp3",
        "original_filename": "aula.mp3",
        "engine": "gemini",
        "compact_silence": 1,
        "review": 0,
        "status": "queued",
        "payload_json": {"turnos": 5},
    }
    sessions.save("t-1", session_data)

    # Busca com tenant correto encontra; com tenant errado devolve None (TN-03, TN-04)
    assert sessions.get("t-1", "sess-1") is not None
    assert sessions.get("t-2", "sess-1") is None

    # Listagem por tenant
    assert len(sessions.list("t-1")) == 1
    assert len(sessions.list("t-2")) == 0

    # Atualizações
    sessions.update_status("t-1", "sess-1", "processing")
    assert sessions.get("t-1", "sess-1")["status"] == "processing"

    sessions.attach_results("t-1", "sess-1", {"turnos": 10}, finished_at=100.0)
    res = sessions.get("t-1", "sess-1")
    assert res["status"] == "done"
    assert res["payload_json"] == {"turnos": 10}

    # Delete
    assert sessions.delete("t-1", "sess-1") is True
    assert sessions.get("t-1", "sess-1") is None


def test_usage_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))

    usage = UsageRepository(db)
    usage.record("t-1", "sess-1", "audio_transcription", audio_seconds=120.5, tokens=3500)
    usage.record("t-1", "sess-1", "lesson_generation", audio_seconds=0.0, tokens=1500)

    total = usage.get_total_usage("t-1")
    assert total["total_audio_seconds"] == 120.5
    assert total["total_tokens"] == 5000


def test_audit_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    users = UserRepository(db)
    users.save_tenant(Tenant(id="t-1", name="Escola A"))
    users.save_user(User("u-1", "t-1", "a@a.com", "A", "owner", "hash"))

    audit = AuditRepository(db)
    audit.record("t-1", "u-1", "class_session.delete", target="sess-99")
    with db.connection() as conn:
        row = conn.execute("SELECT * FROM audit_log WHERE tenant_id = ?", ("t-1",)).fetchone()
        assert row["action"] == "class_session.delete"
        assert row["target"] == "sess-99"
