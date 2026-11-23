"""Aplicação web: API REST dos jobs de transcrição, autenticação e interface estática.

A montagem das dependências (pipeline, clientes) fica em telecom.cli.serve; aqui entram por injeção.
# shortcut: sessão em cookie HttpOnly de 12h com isolamento estrito via Principal (ADR-0002)
"""

import logging
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from telecom.accounts.models import Principal
from telecom.diarization.factory import ENGINES
from telecom.diarization.models import SpeakerSegment
from telecom.lessons.materials import (
    DEFAULT_EXERCISES, LEVELS, MAX_EXERCISES, MAX_FOCUS_CHARS, MIN_EXERCISES, LessonWriter,
)
from telecom.settings import DATABASE_PATH, MEDIA_EXTENSIONS
from telecom.storage.db import Database
from telecom.web.auth import AuthManager, LoginRequest, LoginResponse, MeResponse, verify_csrf
from telecom.web.jobs import Job, JobOptions, JobService, JobStatus
from telecom.web.schemas import AppConfig, EngineInfo, JobView, LessonRequestBody

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
LESSON_UNEXPECTED_ERROR = "Não foi possível gerar o material agora. Veja o log do servidor."

ENGINE_LABELS = {
    "gemini": ("Gemini", "Na nuvem. Rápido, envia o áudio inteiro numa chamada."),
    "pyannote": ("pyannote + Whisper", "Local. Nada sai da máquina, mas exige mais CPU."),
}

DOWNLOADS = {
    "json": ("report_json", "application/json"),
    "md": ("report_md", "text/markdown; charset=utf-8"),
    "words": ("words_json", "application/json"),
}

EngineStatus = Callable[[str], str | None]
LessonWriterFactory = Callable[[], LessonWriter]


def create_app(
    service: JobService,
    engine_status: EngineStatus,
    lesson_writer_factory: LessonWriterFactory | None = None,
    db: Database | None = None,
) -> FastAPI:
    database = db or getattr(service._repo, "_db", None) or Database(DATABASE_PATH)
    auth = AuthManager(database)

    app = FastAPI(title="Pauta", docs_url="/api/docs", openapi_url="/api/openapi.json")

    # --- Autenticação (/api/v1/auth) ---

    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    def login(req: Request, resp: Response, body: LoginRequest) -> LoginResponse:
        return auth.login(req, resp, body)

    @app.post("/api/v1/auth/logout")
    def logout(req: Request, resp: Response) -> dict[str, str]:
        return auth.logout(req, resp)

    @app.get("/api/v1/me", response_model=MeResponse)
    def me(principal: Principal = Depends(auth.current_principal)) -> MeResponse:
        return auth.me(principal)

    # --- Configuração e catálogo ---

    @app.get("/api/v1/config", response_model=AppConfig)
    @app.get("/api/config", response_model=AppConfig)
    def config(principal: Principal = Depends(auth.current_principal)) -> AppConfig:
        engines = []
        for engine in ENGINES:
            reason = engine_status(engine)
            label, description = ENGINE_LABELS[engine]
            engines.append(
                EngineInfo(
                    id=engine, label=label, description=description,
                    available=reason is None, unavailable_reason=reason,
                )
            )
        gemini_ready = engine_status("gemini") is None
        return AppConfig(
            engines=engines,
            review_available=gemini_ready,
            lessons_available=gemini_ready and lesson_writer_factory is not None,
            extensions=list(MEDIA_EXTENSIONS),
            levels=list(LEVELS),
            min_exercises=MIN_EXERCISES,
            max_exercises=MAX_EXERCISES,
            default_exercises=DEFAULT_EXERCISES,
            max_focus_chars=MAX_FOCUS_CHARS,
        )

    # --- Jobs de transcrição e geração ---

    @app.post("/api/v1/jobs", response_model=JobView, status_code=202)
    @app.post("/api/jobs", response_model=JobView, status_code=202)
    def create_job(
        request: Request,
        file: UploadFile = File(...),
        engine: str = Form("gemini"),
        compact_silence: bool = Form(False),
        review: bool = Form(False),
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        verify_csrf(request)
        if engine not in ENGINES:
            raise HTTPException(400, f"Motor desconhecido: {engine}")
        reason = engine_status(engine)
        if reason:
            raise HTTPException(400, reason)
        if review and engine_status("gemini"):
            raise HTTPException(400, "A revisão por IA usa o Gemini, que não está configurado.")
        try:
            job = service.submit(principal, file.filename or "", file.file, JobOptions(engine, compact_silence, review))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return JobView.from_job(job)

    @app.get("/api/v1/jobs", response_model=list[JobView])
    @app.get("/api/jobs", response_model=list[JobView])
    def list_jobs(principal: Principal = Depends(auth.current_principal)) -> list[JobView]:
        return [JobView.from_job(job, include_result=False) for job in service.list(principal)]

    @app.get("/api/v1/jobs/{job_id}", response_model=JobView)
    @app.get("/api/jobs/{job_id}", response_model=JobView)
    def get_job(job_id: str, principal: Principal = Depends(auth.current_principal)) -> JobView:
        return JobView.from_job(_find(service, principal, job_id))

    @app.delete("/api/v1/jobs/{job_id}")
    @app.delete("/api/jobs/{job_id}")
    def delete_job(request: Request, job_id: str, principal: Principal = Depends(auth.current_principal)) -> dict[str, str]:
        verify_csrf(request)
        if not service.delete(principal, job_id):
            raise HTTPException(404, "Transcrição não encontrada.")
        return {"detail": "Sessão excluída com sucesso."}

    @app.post("/api/v1/jobs/{job_id}/lesson", response_model=JobView)
    @app.post("/api/jobs/{job_id}/lesson", response_model=JobView)
    def create_lesson(
        request: Request,
        job_id: str,
        body: LessonRequestBody,
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        verify_csrf(request)
        job = _find(service, principal, job_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(409, "A transcrição ainda não terminou.")
        if lesson_writer_factory is None or engine_status("gemini"):
            raise HTTPException(400, "Gerar material usa o Gemini, que não está configurado.")
        try:
            req = body.to_request()
            lesson = lesson_writer_factory().write(_segments(job), req)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:
            logger.exception("Falha ao gerar material do job %s", job_id)
            raise HTTPException(502, LESSON_UNEXPECTED_ERROR) from exc
        return JobView.from_job(service.attach_lesson(principal, job_id, lesson))

    @app.get("/api/v1/jobs/{job_id}/media")
    @app.get("/api/jobs/{job_id}/media")
    def get_media(job_id: str, principal: Principal = Depends(auth.current_principal)) -> FileResponse:
        job = _find(service, principal, job_id)
        return FileResponse(job.source)

    @app.get("/api/v1/jobs/{job_id}/files/{kind}")
    @app.get("/api/jobs/{job_id}/files/{kind}")
    def download(job_id: str, kind: str, principal: Principal = Depends(auth.current_principal)) -> FileResponse:
        if kind not in DOWNLOADS:
            raise HTTPException(404, "Relatório desconhecido.")
        job = _find(service, principal, job_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(409, "A transcrição ainda não terminou.")
        attribute, media_type = DOWNLOADS[kind]
        path: Path = getattr(job.outputs, attribute)
        return FileResponse(path, media_type=media_type, filename=path.name)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _segments(job: Job) -> list[SpeakerSegment]:
    payload = job.outputs.payload if job.outputs else {}
    return [
        SpeakerSegment(s["quemfala"], s["textodefala"], s["segundos_inicio"], s["segundos_fim"])
        for s in payload.get("segmentos", [])
    ]


def _find(service: JobService, principal: Principal, job_id: str) -> Job:
    job = service.get(principal, job_id)
    if job is None:
        raise HTTPException(404, "Transcrição não encontrada.")
    return job
