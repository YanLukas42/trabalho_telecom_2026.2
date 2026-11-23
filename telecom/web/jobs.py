"""Fila de transcrições e serviço da aplicação (JobService).

Persiste sessões via SessionRepository injetado e isola arquivos por tenant.
# shortcut: ThreadPoolExecutor em processo único no MVP, trocar por fila+worker na VPS (ADR-0003)
# shortcut: arquivos em disco sob output/tenants/, trocar por S3 com URLs assinadas (ADR-0004)
"""

import json
import logging
import re
import shutil
import time
import uuid
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Callable

from telecom.accounts.models import Principal
from telecom.audio.ffmpeg import FFmpegError
from telecom.diarization.factory import ENGINES
from telecom.diarization.pipeline import DiarizationOutputs, DiarizationPipeline
from telecom.lessons.materials import LessonMaterials
from telecom.reporting import write_json
from telecom.settings import MEDIA_EXTENSIONS, TENANTS_DIR
from telecom.storage.repositories import SessionRepository

logger = logging.getLogger(__name__)

# Diarização é pesada (CPU ou cota da API): poucos jobs concorrentes por processo no MVP.
MAX_CONCURRENT_JOBS = 2
LESSON_FILE_NAME = "lesson.json"
UNSAFE_FILENAME_CHARS = re.compile(r"[^\w.\-]+")
UNEXPECTED_ERROR_MESSAGE = "Erro inesperado no processamento. Veja o log do servidor."


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True)
class JobOptions:
    engine: str = "gemini"
    compact_silence: bool = False
    review: bool = False


@dataclass(frozen=True)
class Job:
    id: str
    file_name: str
    source: Path
    options: JobOptions
    status: JobStatus
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    outputs: DiarizationOutputs | None = None
    lesson: LessonMaterials | None = None
    tenant_id: str = ""
    teacher_id: str = ""

    @property
    def active(self) -> bool:
        return self.status in (JobStatus.QUEUED, JobStatus.PROCESSING)


# Recebe as opções do job e a pasta de saída dele; devolve o pipeline pronto para rodar.
PipelineFactory = Callable[[JobOptions, Path], DiarizationPipeline]


class JobService:
    def __init__(
        self,
        pipeline_factory: PipelineFactory,
        session_repo: SessionRepository,
        base_dir: Path = TENANTS_DIR,
        executor: Executor | None = None,
    ):
        self._pipeline_factory = pipeline_factory
        self._repo = session_repo
        self._base_dir = base_dir
        self._executor = executor or ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS)
        # Ao reiniciar o processo, jobs que ficaram na fila ou processando são marcados como falhos (ADR-0003)
        recovered = self._repo.recover_active_on_startup()
        if recovered:
            logger.info("Recuperadas %d sessões ativas no reinício do servidor", recovered)

    def submit(self, principal: Principal, file_name: str, stream: BinaryIO, options: JobOptions) -> Job:
        """Grava o upload sob o diretório do tenant e agenda o processamento."""
        safe_name = sanitize_filename(file_name)
        if Path(safe_name).suffix.lower() not in MEDIA_EXTENSIONS:
            raise ValueError(f"Formato não suportado. Use um destes: {', '.join(MEDIA_EXTENSIONS)}")
        if options.engine not in ENGINES:
            raise ValueError(f"Motor desconhecido: {options.engine}")

        session_id = uuid.uuid4().hex
        session_dir = self._session_dir(principal.tenant_id, session_id)
        source = session_dir / "upload" / safe_name
        source.parent.mkdir(parents=True, exist_ok=True)

        with source.open("wb") as handle:
            shutil.copyfileobj(stream, handle)
        if source.stat().st_size == 0:
            shutil.rmtree(session_dir, ignore_errors=True)
            raise ValueError("O arquivo enviado está vazio.")

        now_sec = time.time()
        session_data = {
            "id": session_id,
            "tenant_id": principal.tenant_id,
            "teacher_id": principal.user_id,
            "file_name": safe_name,
            "status": JobStatus.QUEUED.value,
            "options_json": {
                "engine": options.engine,
                "compact_silence": options.compact_silence,
                "review": options.review,
                "original_filename": file_name,
            },
            "started_at": now_sec,
        }
        self._repo.save(principal.tenant_id, session_data)
        logger.info("Job %s criado para tenant %s", session_id, principal.tenant_id)

        self._executor.submit(self._run, principal.tenant_id, session_id)
        job = self.get(principal, session_id)
        if job is None:
            raise RuntimeError("Falha ao recuperar sessão recém-criada.")
        return job

    def get(self, principal: Principal, session_id: str) -> Job | None:
        """Busca sessão do tenant. Professor só vê suas próprias aulas (TN-04)."""
        data = self._repo.get(principal.tenant_id, session_id)
        if not data:
            return None
        if principal.role == "teacher" and data.get("teacher_id") != principal.user_id:
            return None
        return self._dict_to_job(data)

    def list(self, principal: Principal) -> list[Job]:
        """Lista sessões do tenant. Professores recebem apenas suas aulas."""
        teacher_filter = principal.user_id if principal.role == "teacher" else None
        rows = self._repo.list(principal.tenant_id, teacher_id=teacher_filter)
        return [self._dict_to_job(r) for r in rows]

    def attach_lesson(self, principal: Principal, session_id: str, lesson: LessonMaterials) -> Job:
        """Guarda o material pedagógico gerado na sessão e em disco."""
        job = self.get(principal, session_id)
        if job is None:
            raise ValueError("Sessão não encontrada.")

        session_dir = self._session_dir(principal.tenant_id, session_id)
        write_json(lesson.model_dump(), session_dir / LESSON_FILE_NAME)
        self._repo.attach_lesson(principal.tenant_id, session_id, lesson.model_dump())
        updated = self.get(principal, session_id)
        if updated is None:
            raise RuntimeError("Falha ao recuperar sessão atualizada.")
        return updated

    def delete(self, principal: Principal, session_id: str) -> bool:
        """Exclui a sessão do banco e seus arquivos em disco se pertencer ao tenant (TN-19)."""
        job = self.get(principal, session_id)
        if job is None:
            return False
        deleted = self._repo.delete(principal.tenant_id, session_id)
        session_dir = self._session_dir(principal.tenant_id, session_id)
        shutil.rmtree(session_dir, ignore_errors=True)
        return deleted

    def _run(self, tenant_id: str, session_id: str) -> None:
        raw = self._repo.get(tenant_id, session_id)
        if not raw:
            return
        job = self._dict_to_job(raw)

        self._repo.update_status(tenant_id, session_id, JobStatus.PROCESSING.value, started_at=time.time())
        session_dir = self._session_dir(tenant_id, session_id)

        try:
            pipeline = self._pipeline_factory(job.options, session_dir)
            outputs = pipeline.run(job.source)
        except (ValueError, FFmpegError) as exc:
            logger.warning("Job %s falhou: %s", session_id, exc)
            self._repo.update_status(
                tenant_id, session_id, JobStatus.FAILED.value, error=str(exc), finished_at=time.time()
            )
        except Exception:
            logger.exception("Job %s falhou com erro inesperado", session_id)
            self._repo.update_status(
                tenant_id, session_id, JobStatus.FAILED.value, error=UNEXPECTED_ERROR_MESSAGE, finished_at=time.time()
            )
        else:
            paths = {
                "report_json": str(outputs.report_json),
                "report_md": str(outputs.report_md),
                "words_json": str(outputs.words_json),
            }
            duration = float(outputs.payload.get("duracao_original_segundos", 0.0))
            self._repo.attach_results(tenant_id, session_id, paths, audio_seconds=duration, finished_at=time.time())
            logger.info("Job %s concluído para tenant %s", session_id, tenant_id)

    def _session_dir(self, tenant_id: str, session_id: str) -> Path:
        return self._base_dir / tenant_id / "sessions" / session_id

    def _dict_to_job(self, data: dict[str, Any]) -> Job:
        tenant_id = data["tenant_id"]
        session_id = data["id"]
        session_dir = self._session_dir(tenant_id, session_id)
        file_name = data.get("file_name") or data.get("filename", "")
        source = session_dir / "upload" / file_name

        outputs = None
        if data["status"] == JobStatus.DONE.value:
            stem = Path(file_name).stem
            reports_dir = session_dir / "reports"
            rep_json = Path(data.get("report_json_path") or (reports_dir / f"{stem}_diarizacao_pydantic.json"))
            rep_md = Path(data.get("report_md_path") or (reports_dir / f"{stem}_diarizacao_pydantic.md"))
            w_json = Path(data.get("words_json_path") or (reports_dir / f"{stem}_palavra_por_palavra.json"))
            payload: dict[str, Any] = {}
            if rep_json.is_file():
                try:
                    payload = json.loads(rep_json.read_text(encoding="utf-8"))
                except Exception:
                    payload = {}
            outputs = DiarizationOutputs(
                payload=payload,
                report_json=rep_json,
                report_md=rep_md,
                words_json=w_json,
                words=None,  # type: ignore[arg-type]
            )

        lesson = None
        if data.get("lesson_json"):
            lesson = LessonMaterials.model_validate(data["lesson_json"])

        opts = data.get("options_json") or {}
        orig_name = opts.get("original_filename") or data.get("original_filename") or file_name

        return Job(
            id=session_id,
            file_name=orig_name,
            source=source,
            options=JobOptions(
                engine=opts.get("engine", data.get("engine", "gemini")),
                compact_silence=bool(opts.get("compact_silence", data.get("compact_silence", False))),
                review=bool(opts.get("review", data.get("review", False))),
            ),
            status=JobStatus(data["status"]),
            created_at=data.get("started_at") or 0.0,
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            error=data.get("error"),
            outputs=outputs,
            lesson=lesson,
            tenant_id=tenant_id,
            teacher_id=data.get("teacher_id", ""),
        )


def sanitize_filename(name: str) -> str:
    """Só o nome-base, sem caminho nem caracteres que o sistema de arquivos estranhe."""
    base = Path(name or "").name
    cleaned = UNSAFE_FILENAME_CHARS.sub("_", base).strip("._")
    if not cleaned:
        raise ValueError("Nome de arquivo inválido.")
    return cleaned
