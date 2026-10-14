"""Detecção de silêncio com o filtro silencedetect do FFmpeg (base do VAD e do fatiamento)."""

import re
from pathlib import Path
from typing import NamedTuple

from telecom.audio.ffmpeg import run_ffmpeg

_SILENCE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*([0-9.]+)")


class Interval(NamedTuple):
    start: float
    end: float


def detect_silences(path: Path, noise_db: float = -35.0, min_sec: float = 0.4) -> list[Interval]:
    """Intervalos (início, fim) em segundos em que o sinal fica abaixo de `noise_db` por ao menos `min_sec`."""
    _, stderr = run_ffmpeg([
        "-vn", "-i", str(path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_sec}",
        "-f", "null", "-",
    ])
    starts = [float(value) for value in _SILENCE_START.findall(stderr)]
    ends = [float(value) for value in _SILENCE_END.findall(stderr)]
    return [Interval(start, end) for start, end in zip(starts, ends)]
