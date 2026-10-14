import shutil
import subprocess
from pathlib import Path

import pytest


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


requires_ffmpeg = pytest.mark.skipif(not _has_ffmpeg(), reason="ffmpeg/ffprobe não instalados")


@pytest.fixture
def speech_wav(tmp_path: Path) -> Path:
    """Áudio sintético de 60s: 10s de tom, 4s de silêncio, repetido. Os silêncios são detectáveis."""
    path = tmp_path / "speech.wav"
    expression = "if(lt(mod(t,14),10),0.3*sin(2*PI*220*t),0)"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"aevalsrc='{expression}':d=60:s=16000", "-ac", "1", str(path)],
        check=True,
    )
    return path
