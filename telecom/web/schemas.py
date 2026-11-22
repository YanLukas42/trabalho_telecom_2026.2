"""Contratos da API web. O resultado de um job é o mesmo JSON do relatório de diarização, sem alteração."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from telecom.lessons.materials import DEFAULT_EXERCISES, LessonRequest, Participant
from telecom.web.jobs import Job, JobStatus


class EngineInfo(BaseModel):
    id: str
    label: str
    description: str
    available: bool
    unavailable_reason: str | None = None


class AppConfig(BaseModel):
    engines: list[EngineInfo]
    review_available: bool
    lessons_available: bool
    extensions: list[str]
    levels: list[str]
    min_exercises: int
    max_exercises: int
    default_exercises: int
    max_focus_chars: int


class ParticipantBody(BaseModel):
    label: str
    name: str
    role: str


class LessonRequestBody(BaseModel):
    level: str
    participants: list[ParticipantBody]
    exercises_per_student: int = DEFAULT_EXERCISES
    focus: str = ""

    def to_request(self) -> LessonRequest:
        """Valida as regras de negócio; lança ValueError com mensagem em português."""
        people = tuple(Participant(p.label, p.name.strip() or p.label, p.role) for p in self.participants)
        return LessonRequest(self.level, people, self.exercises_per_student, self.focus.strip())


class JobView(BaseModel):
    id: str
    file_name: str
    status: JobStatus
    engine: str
    compact_silence: bool
    review: bool
    created_at: datetime
    elapsed_sec: float | None
    error: str | None
    result: dict[str, Any] | None
    lesson: dict[str, Any] | None = None

    @classmethod
    def from_job(cls, job: Job, include_result: bool = True) -> "JobView":
        return cls(
            id=job.id,
            file_name=job.file_name,
            status=job.status,
            engine=job.options.engine,
            compact_silence=job.options.compact_silence,
            review=job.options.review,
            created_at=datetime.fromtimestamp(job.created_at, tz=timezone.utc),
            elapsed_sec=_elapsed(job),
            error=job.error,
            result=job.outputs.payload if include_result and job.outputs else None,
            lesson=job.lesson.model_dump() if include_result and job.lesson else None,
        )


def _elapsed(job: Job) -> float | None:
    if job.started_at is None:
        return None
    end = job.finished_at or datetime.now(tz=timezone.utc).timestamp()
    return round(end - job.started_at, 1)
