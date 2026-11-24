"""Aplicação web: API REST v1 para sessões de aula, autenticação e interface estática.

A montagem das dependências fica em telecom.cli.serve; aqui entram por injeção.
# shortcut: sessão em cookie HttpOnly de 12h com isolamento estrito via Principal (ADR-0002)
# shortcut: arquivos sob output/tenants/<tenant_id>/sessions/<id>/ (ADR-0004)
"""

import logging
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from telecom.accounts.models import Principal
from telecom.asr.gemini import GeminiAPIError
from telecom.diarization.factory import ENGINES
from telecom.diarization.models import SpeakerSegment
from telecom.lessons.materials import (
    DEFAULT_EXERCISES, LEVELS, MAX_EXERCISES, MAX_FOCUS_CHARS, MIN_EXERCISES,
    LessonMaterials, LessonWriter,
)
from telecom.settings import DATABASE_PATH, MEDIA_EXTENSIONS
from telecom.storage.db import Database
from telecom.web.auth import AuthManager, LoginRequest, LoginResponse, MeResponse, verify_csrf
from telecom.web.jobs import (
    ConcurrencyLimitError, DurationLimitError, Job, JobOptions, JobService,
    JobStatus, QuotaExceededError, UploadLimitError,
)
from telecom.web.schemas import AppConfig, EngineInfo, JobView, LessonRequestBody, ParticipantBody

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
NOT_FOUND_MESSAGE = "Aula não encontrada. Verifique se o identificador está correto ou se você possui acesso."
LESSON_UNEXPECTED_ERROR = "Não foi possível gerar o material pedagógico agora. Tente novamente em instantes."

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


SECURITY_HEADERS = (
    (b"content-security-policy", b"default-src 'self'; media-src 'self'; img-src 'self' data:; frame-ancestors 'none'"),
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
)
_NO_CACHE_SUFFIXES = (".html", ".js", ".css")


def should_revalidate_asset(path: str) -> bool:
    """Garante revalidação pelo navegador em HTML, CSS e módulos ES sem impedir cache de fontes."""
    return path == "/" or path.endswith(_NO_CACHE_SUFFIXES)


class SecurityHeadersMiddleware:
    """Aplica cabeçalhos de proteção estrita recomendados pelo OWASP ASVS (SG-10)."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        no_cache = should_revalidate_asset(scope.get("path", ""))

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(SECURITY_HEADERS)
                if no_cache:
                    headers.append((b"cache-control", b"no-cache"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app(
    service: JobService,
    engine_status: EngineStatus,
    lesson_writer_factory: LessonWriterFactory | None = None,
    db: Database | None = None,
) -> FastAPI:
    database = db or getattr(service._repo, "_db", None) or Database(DATABASE_PATH)
    auth = AuthManager(database)

    app = FastAPI(title="Pauta", docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json")
    app.add_middleware(SecurityHeadersMiddleware)

    # --- Autenticação (/api/v1/auth) e Usuário (/api/v1/me) ---

    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    def login(req: Request, resp: Response, body: LoginRequest) -> LoginResponse:
        return auth.login(req, resp, body)

    @app.post("/api/v1/auth/logout")
    def logout(req: Request, resp: Response) -> dict[str, str]:
        return auth.logout(req, resp)

    @app.get("/api/v1/me", response_model=MeResponse)
    def me(principal: Principal = Depends(auth.current_principal)) -> MeResponse:
        return auth.me(principal)

    # --- Configurações e motores (/api/v1/config) ---

    @app.get("/api/v1/config", response_model=AppConfig)
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

    # --- Sessões de Aula (/api/v1/sessions) ---

    @app.get("/api/v1/sessions", response_model=list[JobView])
    def list_sessions(principal: Principal = Depends(auth.current_principal)) -> list[JobView]:
        """Lista as sessões da escola visíveis para o professor autenticado."""
        return [JobView.from_job(job, include_result=False) for job in service.list(principal)]

    @app.post("/api/v1/sessions", response_model=JobView, status_code=202)
    def create_session(
        request: Request,
        file: UploadFile = File(...),
        consent: bool = Form(...),
        engine: str = Form("gemini"),
        compact_silence: bool = Form(False),
        review: bool = Form(False),
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        """Upload de áudio de aula. Exige consentimento explícito (consent=true)."""
        verify_csrf(request)
        if not consent:
            raise HTTPException(
                status_code=400,
                detail="É obrigatório confirmar o termo de consentimento para processamento da aula. Marque a opção antes de prosseguir.",
            )
        if engine not in ENGINES:
            raise HTTPException(
                status_code=400,
                detail=f"Motor de processamento '{engine}' desconhecido. Escolha um motor suportado.",
            )
        reason = engine_status(engine)
        if reason:
            raise HTTPException(
                status_code=400,
                detail=f"O motor '{engine}' está indisponível: {reason}. Selecione outro motor de transcrição.",
            )
        if review and engine_status("gemini"):
            raise HTTPException(
                status_code=400,
                detail="A revisão por inteligência artificial requer a chave do Gemini configurada. Ajuste as variáveis de ambiente.",
            )
        try:
            job = service.submit(
                principal,
                file.filename or "",
                file.file,
                JobOptions(engine, compact_silence, review),
                consent=consent,
            )
        except ConcurrencyLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except QuotaExceededError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except UploadLimitError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except DurationLimitError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{exc} Selecione um arquivo válido e tente novamente.") from exc
        return JobView.from_job(job)

    @app.get("/api/v1/sessions/{session_id}", response_model=JobView)
    def get_session(session_id: str, principal: Principal = Depends(auth.current_principal)) -> JobView:
        return JobView.from_job(_find(service, principal, session_id))

    @app.post("/api/v1/sessions/{session_id}/retry", response_model=JobView)
    def retry_session(
        request: Request,
        session_id: str,
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        """Reenvia uma aula com falha ou parada para a fila de processamento."""
        verify_csrf(request)
        _find(service, principal, session_id)
        try:
            updated = service.retry(principal, session_id)
        except (ConcurrencyLimitError, QuotaExceededError) as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except ValueError as exc:
            code = 409 if "já está em processamento" in str(exc) else 400
            raise HTTPException(status_code=code, detail=str(exc)) from exc
        return JobView.from_job(updated)

    @app.delete("/api/v1/sessions/{session_id}")
    def delete_session(
        request: Request,
        session_id: str,
        principal: Principal = Depends(auth.current_principal),
    ) -> dict[str, str]:
        """Exclui a sessão e seus arquivos do disco e registra auditoria LGPD."""
        verify_csrf(request)
        _find(service, principal, session_id)
        service.delete(principal, session_id)
        auth.audit.record(principal.tenant_id, principal.user_id, "session.delete", target=session_id)
        return {"detail": "Aula e seus arquivos foram excluídos com sucesso em conformidade com a LGPD."}

    @app.put("/api/v1/sessions/{session_id}/participants", response_model=JobView)
    def update_participants(
        request: Request,
        session_id: str,
        participants: list[ParticipantBody],
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        """Salva a identificação de alunos e professores da aula."""
        verify_csrf(request)
        _find(service, principal, session_id)
        parts_data = [p.model_dump() for p in participants]
        updated = service.attach_participants(principal, session_id, parts_data)
        return JobView.from_job(updated)

    @app.post("/api/v1/sessions/{session_id}/lesson", response_model=JobView)
    def create_lesson(
        request: Request,
        session_id: str,
        body: LessonRequestBody,
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        """Gera atividades por aluno e o plano da próxima aula."""
        verify_csrf(request)
        job = _find(service, principal, session_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(
                status_code=409,
                detail="A transcrição da aula ainda não foi finalizada. Aguarde o término do áudio para gerar o material.",
            )
        if lesson_writer_factory is None or engine_status("gemini"):
            raise HTTPException(
                status_code=400,
                detail="A geração de materiais pedagógicos requer o Gemini configurado. Adicione a chave GEMINI_API_KEY no arquivo .env.",
            )
        try:
            req = body.to_request()
            writer = lesson_writer_factory()
            lesson = writer.write(_segments(job), req)
        except GeminiAPIError as exc:
            raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{exc} Ajuste os parâmetros e tente novamente.") from exc
        except Exception as exc:
            logger.exception("Falha ao gerar material para sessão %s", session_id)
            raise HTTPException(status_code=502, detail=LESSON_UNEXPECTED_ERROR) from exc

        updated = service.attach_lesson(principal, session_id, lesson)
        tokens = getattr(writer, "last_tokens", 0) or 1500
        auth.usage.record(principal.tenant_id, session_id, "lesson", audio_seconds=0.0, tokens=tokens)
        return JobView.from_job(updated)

    @app.put("/api/v1/sessions/{session_id}/lesson", response_model=JobView)
    def update_lesson(
        request: Request,
        session_id: str,
        body: dict[str, Any],
        principal: Principal = Depends(auth.current_principal),
    ) -> JobView:
        """Salva edições feitas pelo professor no material pedagógico, validando a estrutura."""
        verify_csrf(request)
        _find(service, principal, session_id)
        try:
            lesson = LessonMaterials.model_validate(body)
        except ValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"A estrutura do material pedagógico é inválida: {exc.errors()[0]['msg']}. Verifique as edições antes de salvar.",
            ) from exc
        updated = service.attach_lesson(principal, session_id, lesson)
        return JobView.from_job(updated)

    @app.get("/api/v1/sessions/{session_id}/media")
    def get_media(session_id: str, principal: Principal = Depends(auth.current_principal)) -> FileResponse:
        job = _find(service, principal, session_id)
        if not job.source.is_file():
            raise HTTPException(status_code=404, detail="Arquivo de áudio da aula não foi encontrado no servidor.")
        return FileResponse(job.source)

    @app.get("/api/v1/sessions/{session_id}/files/{kind}")
    def download(session_id: str, kind: str, principal: Principal = Depends(auth.current_principal)) -> FileResponse:
        if kind not in DOWNLOADS:
            raise HTTPException(
                status_code=404,
                detail=f"Tipo de relatório '{kind}' desconhecido. Escolha entre: {', '.join(DOWNLOADS.keys())}.",
            )
        job = _find(service, principal, session_id)
        if job.status is not JobStatus.DONE or job.outputs is None:
            raise HTTPException(
                status_code=409,
                detail="A transcrição ainda está sendo processada. Aguarde o término para baixar o relatório.",
            )
        attribute, media_type = DOWNLOADS[kind]
        path: Path = getattr(job.outputs, attribute)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Arquivo de relatório não encontrado em disco.")
        return FileResponse(path, media_type=media_type, filename=path.name)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _segments(job: Job) -> list[SpeakerSegment]:
    payload = job.outputs.payload if job.outputs else {}
    return [
        SpeakerSegment(s["quemfala"], s["textodefala"], s["segundos_inicio"], s["segundos_fim"])
        for s in payload.get("segmentos", [])
    ]


def _find(service: JobService, principal: Principal, session_id: str) -> Job:
    """Busca a sessão exigindo isolamento por tenant e professor (TN-03, TN-04)."""
    job = service.get(principal, session_id)
    if job is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return job
