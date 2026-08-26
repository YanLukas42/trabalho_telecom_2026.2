"""
Processador de Áudio Rápido para Diarizador 2.0.
Sem VAD (mantém áudio contínuo e tempo real) e Sem normalização pesada.
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional


class FastAudioPreparer:
    """Prepara arquivos MP3 com foco em velocidade (<1s) e preservação tímbrica."""

    @staticmethod
    def prepare_mp3(
        input_path: Path,
        output_path: Path,
        bitrate: str = "32k",
        sample_rate: int = 16000,
        channels: int = 1,
        filter_wideband: bool = True
    ) -> Dict[str, Any]:
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            "-ar", str(sample_rate),
            "-ac", str(channels),
        ]

        if filter_wideband:
            # Filtro Wideband de voz (80Hz - 7.5kHz) que protege formantes de falantes
            cmd.extend(["-af", "highpass=f=80,lowpass=f=7500"])

        cmd.append(str(output_path))

        t0 = time.time()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        prep_time = round(time.time() - t0, 3)

        if res.returncode != 0:
            raise RuntimeError(f"Falha na preparação de áudio FFmpeg: {res.stderr}")

        size_bytes = output_path.stat().st_size
        return {
            "output_path": str(output_path),
            "file_size_bytes": size_bytes,
            "file_size_kb": round(size_bytes / 1024, 2),
            "prep_time_sec": prep_time,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels,
            "filter_wideband": filter_wideband
        }
