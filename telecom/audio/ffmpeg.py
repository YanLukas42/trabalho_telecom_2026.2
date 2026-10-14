"""Ponto único de contato com FFmpeg/FFprobe: nenhum outro módulo executa processos externos."""

import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    """Falha ao executar o FFmpeg ou o FFprobe."""


def run_ffmpeg(args: list[str], stdin: bytes | None = None) -> tuple[bytes, str]:
    """Executa o ffmpeg e devolve (stdout, stderr).

    O stderr é relevante para filtros de análise (ex.: silencedetect), que escrevem o resultado ali.
    """
    cmd = ["ffmpeg", "-hide_banner", *args]
    proc = subprocess.run(cmd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise FFmpegError(f"ffmpeg falhou (código {proc.returncode}): {stderr[-2000:]}")
    return proc.stdout, stderr


def probe_duration(path: Path) -> float:
    """Duração do arquivo em segundos, via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode != 0:
        raise FFmpegError(f"ffprobe falhou em {path}: {proc.stderr.strip()}")
    return float(proc.stdout.strip())


def decode_pcm16(path: Path, sample_rate: int, channels: int) -> bytes:
    """Decodifica o áudio para PCM 16 bits little-endian (bytes crus)."""
    pcm, _ = run_ffmpeg([
        "-vn", "-i", str(path),
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-ar", str(sample_rate), "-ac", str(channels),
        "-",
    ])
    return pcm
