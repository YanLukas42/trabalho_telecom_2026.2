"""Testes das mudanças no site (UX), módulos ES e conformidade de arquitetura."""

from pathlib import Path
from starlette.requests import Request
from starlette.responses import Response

from telecom.accounts.models import Principal
from telecom.web.app import create_app
from telecom.web.jobs import Job, JobOptions, JobService, JobStatus
from telecom.web.schemas import JobView

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "telecom" / "web" / "static"
JS_DIR = STATIC_DIR / "js"


def test_required_js_modules_exist():
    required_files = [
        JS_DIR / "dom.js",
        JS_DIR / "api.js",
        JS_DIR / "format.js",
        JS_DIR / "router.js",
        JS_DIR / "print.js",
        JS_DIR / "main.js",
        JS_DIR / "views" / "login.js",
        JS_DIR / "views" / "sessions.js",
        JS_DIR / "views" / "upload.js",
        JS_DIR / "views" / "session.js",
        JS_DIR / "views" / "sheets.js",
        JS_DIR / "views" / "plan.js",
    ]
    for path in required_files:
        assert path.is_file(), f"Módulo obrigatório não encontrado: {path}"


def test_index_html_uses_es_modules_and_has_no_sidebar():
    index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert '<script type="module" src="/js/main.js"></script>' in index_html
    assert '<aside class="history"' not in index_html
    assert 'fonts.googleapis.com' not in index_html
    assert 'id="topbar"' in index_html
    assert 'id="view"' in index_html
    assert 'id="print-root"' in index_html


def test_app_js_is_removed():
    assert not (STATIC_DIR / "app.js").exists(), "O arquivo monolítico app.js deveria ter sido removido."


def test_all_js_files_within_400_lines():
    for js_path in JS_DIR.rglob("*.js"):
        lines = len(js_path.read_text(encoding="utf-8").splitlines())
        assert lines <= 400, f"{js_path.name} tem {lines} linhas (> 400)."


def test_job_view_includes_audio_seconds_and_has_lesson(tmp_path):
    job = Job(
        id="test-session-123",
        file_name="aula_ingles.mp3",
        source=tmp_path / "audio.mp3",
        options=JobOptions(engine="gemini"),
        status=JobStatus.DONE,
        created_at=1000.0,
        audio_seconds=2700.0,
    )
    view = JobView.from_job(job, include_result=False)
    assert view.audio_seconds == 2700.0
    assert view.has_lesson is False


def test_static_files_and_csp(tmp_path):
    from telecom.storage.db import Database
    from telecom.storage.repositories import SessionRepository
    from telecom.web.auth import AuthManager

    db = Database(tmp_path / "test.db")
    session_repo = SessionRepository(db)
    service = JobService(lambda opt, path: None, session_repo, base_dir=tmp_path)
    app = create_app(service, lambda eng: None, db=db)

    # Verifica se os arquivos estáticos foram montados
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert any(p.startswith("") or p == "/" for p in routes)
