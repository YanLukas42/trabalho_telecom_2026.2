"""Aplicação web: API REST dos jobs de transcrição e a interface estática.

A montagem das dependências (pipeline, clientes) fica em telecom.cli.serve; aqui só entram por injeção.
"""

import logging
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from telecom.accounts.models import Principal
from telecom.diarization.factory import ENGINES
from telecom.diarization.models import SpeakerSegment
from telecom.lessons.materials import (
    DEFAULT_EXERCISES, LEVELS, MAX_EXERCISES, MAX_FOCUS_CHARS, MIN_EXERCISES, LessonWriter,
)
from telecom.settings import MEDIA_EXTENSIONS
from telecom.web.jobs import Job, JobOptions, JobService, JobStatus
from telecom.web.schemas import AppConfig, EngineInfo, JobView, LessonRequestBody

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
LESSON_UNEXPECTED_ERROR = "Não foi possível gerar o material agora. Veja o log do servidor."

ENGINE_LABELS = {
    "gemini": ("Gemini", "Na nuvem. Rápido, envia o áudio inteiro numa chamada."),
    "pyannote": ("pyannote + Whisper", "Local. Nada sai da máquina, mas exige mais CPU."),
}

# Tipo de cada relatório para download: (atributo em DiarizationOutputs, media type).
DOWNLOADS = {
    "json": ("report_json", "application/json"),
    "md": ("report_md", "text/markdown; charset=utf-8"),
    "words": ("words_json", "application/json"),
}

# Recebe o motor e devolve o motivo de indisponibilidade, ou None.
EngineStatus = Callable[[str], str | None]
# Cria o gerador de material sob demanda: o cliente do Gemini só nasce quando alguém pede.
LessonWriterFactory = Callable[[], LessonWriter]


# shortcut: Principal dev padrão no localhost até implementação de auth (ADR-0002)
DEV_PRINCIPAL = Principal(tenant_id="default-tenant", user_id="default-teacher", role="teacher")


def create_app(
    service: JobService,
    engine_status: EngineStatus,
    lesson_writer_factory: LessonWriterFactory | None = None,
) -> FastAPI:
    app = FastAPI(title="Transcritor", docs_url="/api/docs", openapi_url="/api/openapi.json")

    @app.get("/api/config", response_model=AppConfig)
    def config() -> AppConfig:
        engines = []
        for engine in ENGINES:
            reason = engine_status(engine)
            label, description = ENGINE_LABELS[engine]
            engines.append(EngineInfo(id=engine, label=label, description=description,
                                      available=reason is None, unavailable_reason=reason))
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

    @app.post("/api/jobs", response_model=JobView, status_code=202)
    def create_job(
        file: UploadFile = File(...),
        engine: str = Form("gemini"),
        compact_silence: bool = Form(False),
        review: bool = Form(False),
    ) -> JobView:
        if engine not in ENGINES:
            raise HTTPException(400, f"Motor desconhecido: {engine}")
        reason = engine_status(engine)
        if reason:
            raise HTTPException(400, reason)
        if review and engine_status("gemini"):
            raise HTTPException(400, "A revisão por IA usa o Gemini, que não está configurado.")
        try:
            job = service.submit(DEV_PRINCIPAL, file.filename or "", file.file, JobOptions(engine, compact_silence, review))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return JobView.from_job(job)

    @app.get("/api/jobs", response_model=list[JobView])
    def list_jobs() -> list[JobView]:
        return [JobView.from_job(job, include_result=False) for job in service.list(DEV_PRINCIPAL)]

    @app.get("/api/jobs/{job_id}", response_model=JobView)
    def get_job(job_id: str) -> JobView:
        return JobView.from_job(_find(service, job_id))

    @app.post("/api/jobs/{job_id}/lesson", response_model=JobView)
    def create_lesson(job_id: str, body: LessonRequestBody) -> JobView:
        """Gera atividades por aluno e o plano da próxima aula a partir da transcrição pronta."""
        job = _find(service, job_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(409, "A transcrição ainda não terminou.")
        if lesson_writer_factory is None or engine_status("gemini"):
            raise HTTPException(400, "Gerar material usa o Gemini, que não está configurado.")
        try:
            request = body.to_request()
            lesson = lesson_writer_factory().write(_segments(job), request)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:
            logger.exception("Falha ao gerar material do job %s", job_id)
            raise HTTPException(502, LESSON_UNEXPECTED_ERROR) from exc
        return JobView.from_job(service.attach_lesson(DEV_PRINCIPAL, job_id, lesson))

    @app.get("/api/jobs/{job_id}/media")
    def get_media(job_id: str) -> FileResponse:
        job = _find(service, job_id)
        return FileResponse(job.source)

    @app.get("/api/jobs/{job_id}/files/{kind}")
    def download(job_id: str, kind: str) -> FileResponse:
        if kind not in DOWNLOADS:
            raise HTTPException(404, "Relatório desconhecido.")
        job = _find(service, job_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(409, "A transcrição ainda não terminou.")
        attribute, media_type = DOWNLOADS[kind]
        path: Path = getattr(job.outputs, attribute)
        return FileResponse(path, media_type=media_type, filename=path.name)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _segments(job: Job) -> list[SpeakerSegment]:
    """Falas do relatório (chaves em português) no tipo que o gerador de material espera."""
    payload = job.outputs.payload if job.outputs else {}
    return [
        SpeakerSegment(s["quemfala"], s["textodefala"], s["segundos_inicio"], s["segundos_fim"])
        for s in payload.get("segmentos", [])
    ]


def _find(service: JobService, job_id: str) -> Job:
    job = service.get(DEV_PRINCIPAL, job_id)
    if job is None:
        raise HTTPException(404, "Transcrição não encontrada.")
    return job
