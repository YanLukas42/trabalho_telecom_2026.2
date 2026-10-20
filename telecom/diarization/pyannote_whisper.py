"""Diarização local: pyannote define quem fala e quando; whisper define o que foi dito, palavra por palavra.

As dependências pesadas (torch, pyannote.audio, faster-whisper) são importadas só ao construir os modelos,
então o restante do projeto e os testes rodam sem elas. Os tempos dos dois modelos vêm do mesmo arquivo,
sem recorte nem reamostragem entre eles, então os instantes são comparáveis.
"""

import logging
import time
from pathlib import Path
from typing import Callable, Optional

from telecom.audio.ffmpeg import probe_duration
from telecom.diarization.models import Transcription, Turn, WordTiming
from telecom.diarization.timeline import alignment_stats, alignment_warnings, assign_speakers, group_utterances

logger = logging.getLogger(__name__)

PYANNOTE_MODEL = "pyannote/speaker-diarization-3.1"
TurnSource = Callable[[Path], list[Turn]]
WordSource = Callable[[Path], tuple[list[WordTiming], str]]


class PyannoteWhisperDiarizer:
    """Implementa o contrato `Diarizer`. As fontes de turnos e de palavras são injetadas, então os testes usam fakes."""

    def __init__(
        self,
        turn_source: TurnSource,
        word_source: WordSource,
        *,
        tolerance_sec: float = 0.3,
        max_gap_sec: float = 0.8,
    ):
        self._turns = turn_source
        self._words = word_source
        self._tolerance = tolerance_sec
        self._max_gap = max_gap_sec

    def diarize(self, audio_path: Path) -> Transcription:
        audio_path = Path(audio_path)
        started = time.perf_counter()

        turns = self._turns(audio_path)
        words, language = self._words(audio_path)
        labeled = assign_speakers(words, turns, self._tolerance)
        segments = tuple(group_utterances(labeled, self._max_gap))

        duration = probe_duration(audio_path)
        warnings = alignment_warnings(labeled, turns, duration)
        for warning in warnings:
            logger.warning("Alinhamento: %s", warning)

        return Transcription(
            segments=segments,
            prompt_tokens=0,
            candidate_tokens=0,
            total_tokens=0,
            latency_sec=round(time.perf_counter() - started, 3),
            words=tuple(labeled),
            alignment={**alignment_stats(labeled, turns), "idioma": language, "avisos": warnings},
        )


def build_local_diarizer(
    *,
    hf_token: str,
    whisper_model: str = "small",
    device: str = "cpu",
    language: str = "pt",
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
) -> PyannoteWhisperDiarizer:
    """Carrega os modelos reais. Exige token do Hugging Face: o modelo do pyannote é restrito."""
    turns = _PyannoteTurns(hf_token, device, num_speakers, min_speakers, max_speakers)
    words = _WhisperWords(whisper_model, device, language)
    return PyannoteWhisperDiarizer(turn_source=turns, word_source=words)


class _PyannoteTurns:
    def __init__(
        self,
        hf_token: str,
        device: str,
        num_speakers: Optional[int],
        min_speakers: Optional[int],
        max_speakers: Optional[int],
    ):
        self._hf_token = hf_token
        self._device = device
        self._counts = {"num_speakers": num_speakers, "min_speakers": min_speakers, "max_speakers": max_speakers}
        self._pipeline = None

    def __call__(self, audio_path: Path) -> list[Turn]:
        if self._pipeline is None:
            import torch
            from pyannote.audio import Pipeline

            self._pipeline = Pipeline.from_pretrained(PYANNOTE_MODEL, use_auth_token=self._hf_token)
            self._pipeline.to(torch.device(self._device))

        annotation = self._pipeline(str(audio_path), **self._counts)
        return [
            Turn(speaker=label, start=segment.start, end=segment.end)
            for segment, _, label in annotation.itertracks(yield_label=True)
        ]


class _WhisperWords:
    def __init__(self, model_name: str, device: str, language: str):
        from faster_whisper import WhisperModel

        compute_type = "int8" if device == "cpu" else "float16"
        self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
        self._language = language

    def __call__(self, audio_path: Path) -> tuple[list[WordTiming], str]:
        segments, info = self._model.transcribe(
            str(audio_path),
            language=self._language,
            word_timestamps=True,
            beam_size=5,
            vad_filter=False,
        )
        words = [
            WordTiming(word.word.strip(), round(word.start, 3), round(word.end, 3))
            for segment in segments
            for word in (segment.words or [])
            if word.word.strip()
        ]
        return words, info.language
