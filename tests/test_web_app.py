from pathlib import Path
import pytest
from fastapi import FastAPI

from telecom.accounts.models import Principal, Tenant, User
from telecom.storage.db import Database
from telecom.storage.repositories import SessionRepository, UserRepository
from telecom.web.app import STATIC_DIR, create_app
from telecom.web.jobs import JobService
from tests.test_web_jobs import ImmediateExecutor, fake_factory


def test_app_routes_are_all_under_api_v1(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    repo = SessionRepository(db)
    service = JobService(fake_factory, repo, tmp_path / "jobs", ImmediateExecutor())
    app = create_app(service, lambda eng: None, db=db)

    # Coleta todas as rotas da API
    api_routes = [route.path for route in app.routes if route.path.startswith("/api")]

    # Nenhuma rota antiga /api sem /v1 deve existir
    unversioned = [p for p in api_routes if not p.startswith("/api/v1")]
    assert unversioned == [], f"Rotas sem versão /v1 encontradas: {unversioned}"

    # Rotas essenciais da API v1 devem estar presentes
    expected_v1_routes = {
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/me",
        "/api/v1/config",
        "/api/v1/sessions",
        "/api/v1/sessions/{session_id}",
        "/api/v1/sessions/{session_id}/retry",
        "/api/v1/sessions/{session_id}/participants",
        "/api/v1/sessions/{session_id}/lesson",
        "/api/v1/sessions/{session_id}/media",
        "/api/v1/sessions/{session_id}/files/{kind}",
    }

    actual_routes = set(api_routes)
    for expected in expected_v1_routes:
        assert expected in actual_routes, f"Rota esperada {expected} não encontrada na aplicação"


def test_static_interface_files_exist():
    assert STATIC_DIR.is_dir()
    assert (STATIC_DIR / "index.html").is_file()
    assert (STATIC_DIR / "js" / "main.js").is_file()
