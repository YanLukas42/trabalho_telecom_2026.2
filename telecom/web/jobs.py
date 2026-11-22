"""Fila de transcrições em memória: guarda o estado de cada job e roda o pipeline em segundo plano.

Sem banco de dados: o estado vive enquanto o servidor estiver no ar. Os arquivos ficam em WEB_JOBS_DIR/<id>/.
"""

import logging
import re
import shutil
import threading
import time
import uuid
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Callable

from telecom.audio.ffmpeg import FFmpegError
from telecom.diarization.factory import ENGINES
from telecom.diarization.pipeline import DiarizationOutputs, DiarizationPipeline
from telecom.lessons.materials import LessonMaterials
from telecom.reporting import write_json
from telecom.settings import MEDIA_EXTENSIONS, WEB_JOBS_DIR

logger = logging.getLogger(__name__)

# Diarização é pesada (CPU ou cota da API): poucos jobs ao mesmo tempo.
MAX_CONCURRENT_JOBS = 2
JOB_ID_LENGTH = 12
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

    @property
    def active(self) -> bool:
        return self.status in (JobStatus.QUEUED, JobStatus.PROCESSING)


# Recebe as opções do job e a pasta de saída dele; devolve o pipeline pronto para rodar.
PipelineFactory = Callable[[JobOptions, Path], DiarizationPipeline]


class JobService:
    def __init__(
        self,
        pipeline_factory: PipelineFactory,
        jobs_dir: Path = WEB_JOBS_DIR,
        executor: Executor | None = None,
    ):
        self._pipeline_factory = pipeline_factory
        self._jobs_dir = jobs_dir
        self._executor = executor or ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS)
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, file_name: str, stream: BinaryIO, options: JobOptions) -> Job:
        """Grava o upload e agenda o processamento. Lança ValueError para arquivo ou opção inválidos."""
        safe_name = sanitize_filename(file_name)
        if Path(safe_name).suffix.lower() not in MEDIA_EXTENSIONS:
            raise ValueError(f"Formato não suportado. Use um destes: {', '.join(MEDIA_EXTENSIONS)}")
        if options.engine not in ENGINES:
            raise ValueError(f"Motor desconhecido: {options.engine}")

        job_id = uuid.uuid4().hex[:JOB_ID_LENGTH]
        source = self._jobs_dir / job_id / "upload" / safe_name
        source.parent.mkdir(parents=True, exist_ok=True)
        with source.open("wb") as handle:
            shutil.copyfileobj(stream, handle)
        if source.stat().st_size == 0:
            shutil.rmtree(source.parent.parent)
            raise ValueError("O arquivo enviado está vazio.")

        job = Job(job_id, safe_name, source, options, JobStatus.QUEUED, created_at=time.time())
        with self._lock:
            self._jobs[job_id] = job
        logger.info("Job %s criado: %s (%s)", job_id, safe_name, options)
        self._executor.submit(self._run, job_id)
        return self.get(job_id) or job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        """Jobs do mais recente para o mais antigo."""
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def attach_lesson(self, job_id: str, lesson: LessonMaterials) -> Job:
        """Guarda o material gerado no job e grava lesson.json na pasta dele."""
        write_json(lesson.model_dump(), self._jobs_dir / job_id / LESSON_FILE_NAME)
        return self._update(job_id, lesson=lesson)

    def _run(self, job_id: str) -> None:
        job = self._update(job_id, status=JobStatus.PROCESSING, started_at=time.time())
        try:
            pipeline = self._pipeline_factory(job.options, self._jobs_dir / job_id)
            outputs = pipeline.run(job.source)
        except (ValueError, FFmpegError) as exc:
            logger.warning("Job %s falhou: %s", job_id, exc)
            self._update(job_id, status=JobStatus.FAILED, error=str(exc), finished_at=time.time())
        except Exception:
            logger.exception("Job %s falhou com erro inesperado", job_id)
            self._update(job_id, status=JobStatus.FAILED, error=UNEXPECTED_ERROR_MESSAGE, finished_at=time.time())
        else:
            self._update(job_id, status=JobStatus.DONE, outputs=outputs, finished_at=time.time())
            logger.info("Job %s concluído", job_id)

    def _update(self, job_id: str, **changes) -> Job:
        with self._lock:
            job = replace(self._jobs[job_id], **changes)
            self._jobs[job_id] = job
            return job


def sanitize_filename(name: str) -> str:
    """Só o nome-base, sem caminho nem caracteres que o sistema de arquivos estranhe."""
    base = Path(name or "").name
    cleaned = UNSAFE_FILENAME_CHARS.sub("_", base).strip("._")
    if not cleaned:
        raise ValueError("Nome de arquivo inválido.")
    return cleaned
