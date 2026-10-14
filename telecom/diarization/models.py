"""Tipos do pipeline de diarização. O pipeline depende deste contrato, não da API."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class SpeakerSegment:
    """Uma fala. Os tempos são em segundos desde o início do áudio enviado."""

    speaker: str
    text: str
    start_sec: float
    end_sec: float


@dataclass(frozen=True)
class Transcription:
    segments: tuple[SpeakerSegment, ...]
    prompt_tokens: int
    candidate_tokens: int
    total_tokens: int
    latency_sec: float


class Diarizer(Protocol):
    """Diariza um arquivo de áudio inteiro."""

    def diarize(self, audio_path: Path) -> Transcription: ...
