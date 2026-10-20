"""Tipos do pipeline de diarização. O pipeline depende deste contrato, não das bibliotecas."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SpeakerSegment:
    """Uma fala. Os tempos são em segundos desde o início do áudio enviado."""

    speaker: str
    text: str
    start_sec: float
    end_sec: float


@dataclass(frozen=True)
class Turn:
    """Intervalo em que um falante fala, segundo o diarizador (ex.: pyannote)."""

    speaker: str
    start: float
    end: float


@dataclass(frozen=True)
class WordTiming:
    """Palavra com tempo, segundo o transcritor (ex.: whisper)."""

    text: str
    start: float
    end: float


@dataclass(frozen=True)
class SpeakerWord(WordTiming):
    speaker: str


@dataclass(frozen=True)
class Transcription:
    segments: tuple[SpeakerSegment, ...]
    prompt_tokens: int
    candidate_tokens: int
    total_tokens: int
    latency_sec: float
    words: tuple[SpeakerWord, ...] = ()
    alignment: dict[str, Any] = field(default_factory=dict)


class Diarizer(Protocol):
    """Diariza um arquivo de áudio inteiro."""

    def diarize(self, audio_path: Path) -> Transcription: ...
