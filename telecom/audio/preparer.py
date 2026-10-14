"""Tratamentos de áudio: transforma a mídia de origem no arquivo que é enviado à API."""

import time
from dataclasses import dataclass, field
from pathlib import Path

from telecom.audio.codecs import get_codec
from telecom.audio.ffmpeg import decode_pcm16, run_ffmpeg
from telecom.audio.vad import SpeechMap, build_speech_map, compact_pcm


@dataclass(frozen=True)
class Treatment:
    """Parâmetros de um tratamento de áudio. É dado puro: a execução fica em `prepare_audio`."""

    id: str
    label: str
    bitrate: str
    sample_rate: int
    channels: int
    codec: str = "mp3"
    filters: tuple[str, ...] = ()
    compact_silence: bool = False
    category: str = "Diarização"
    is_baseline: bool = False


@dataclass(frozen=True)
class PreparedAudio:
    path: Path
    size_bytes: int
    prep_time_sec: float
    speech_map: SpeechMap | None = field(default=None)

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 2)


def prepare_audio(source: Path, output: Path, treatment: Treatment) -> PreparedAudio:
    """Aplica o tratamento a `source` e grava o resultado em `output`."""
    output.parent.mkdir(parents=True, exist_ok=True)
    codec = get_codec(treatment.codec)
    started = time.perf_counter()

    speech_map = None
    if treatment.compact_silence:
        speech_map = build_speech_map(source)
        pcm = decode_pcm16(source, treatment.sample_rate, treatment.channels)
        pcm = compact_pcm(pcm, speech_map, treatment.sample_rate, treatment.channels)
        run_ffmpeg([
            "-y",
            "-f", "s16le", "-ar", str(treatment.sample_rate), "-ac", str(treatment.channels), "-i", "-",
            *_filter_args(treatment.filters),
            *codec.encode_args(treatment.bitrate),
            str(output),
        ], stdin=pcm)
    else:
        run_ffmpeg([
            "-y", "-i", str(source), "-vn",
            *codec.encode_args(treatment.bitrate),
            "-ar", str(treatment.sample_rate), "-ac", str(treatment.channels),
            *_filter_args(treatment.filters),
            str(output),
        ])

    return PreparedAudio(
        path=output,
        size_bytes=output.stat().st_size,
        prep_time_sec=round(time.perf_counter() - started, 3),
        speech_map=speech_map,
    )


def _filter_args(filters: tuple[str, ...]) -> list[str]:
    return ["-af", ",".join(filters)] if filters else []
