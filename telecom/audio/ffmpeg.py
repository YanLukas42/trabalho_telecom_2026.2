"""Ponto único de contato com FFmpeg/FFprobe: nenhum outro módulo executa processos externos.

# shortcut: FFmpeg local via subprocess sem contêiner, trocar por worker isolado na VPS (ADR-0003, SG-07)
"""

import subprocess
from pathlib import Path

FFMPEG_TIMEOUT_SEC = 15 * 60  # 15 minutos (SG-07)
FFPROBE_TIMEOUT_SEC = 60      # 60 segundos (SG-07)


class FFmpegError(RuntimeError):
    """Falha ao executar o FFmpeg ou o FFprobe."""


def run_ffmpeg(args: list[str], stdin: bytes | None = None) -> tuple[bytes, str]:
    """Executa o ffmpeg com timeout e restrição estrita de protocolos (SG-07)."""
    # Insere "-protocol_whitelist file,pipe" antes de cada "-i"
    sanitized_args: list[str] = []
    for arg in args:
        if arg == "-i":
            sanitized_args.extend(["-protocol_whitelist", "file,pipe", "-i"])
        else:
            sanitized_args.append(arg)

    cmd = ["ffmpeg", "-hide_banner", *sanitized_args]
    try:
        proc = subprocess.run(
            cmd,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=FFMPEG_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(f"ffmpeg excedeu o tempo limite de {FFMPEG_TIMEOUT_SEC // 60} minutos.") from exc

    stderr = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise FFmpegError(f"ffmpeg falhou (código {proc.returncode}): {stderr[-2000:]}")
    return proc.stdout, stderr


def probe_duration(path: Path) -> float:
    """Duração do arquivo em segundos, via ffprobe, restrito ao protocolo file (SG-07)."""
    cmd = [
        "ffprobe", "-v", "error",
        "-protocol_whitelist", "file",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=FFPROBE_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError(f"ffprobe excedeu o tempo limite de {FFPROBE_TIMEOUT_SEC} segundos.") from exc

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
