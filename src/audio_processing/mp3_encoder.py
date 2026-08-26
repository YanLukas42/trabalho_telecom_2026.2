"""
MP3 Encoder and Transcoder using FFmpeg.
Handles bitrate sweeps, sample rate resampling, channel downmixing, and format conversion.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any


class MP3Encoder:
    """Encodes and manipulates MP3 files with precise telecom & audio parameters."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def transcode(
        self,
        input_path: Path,
        output_path: Path,
        bitrate: str = "128k",
        sample_rate: int = 44100,
        channels: int = 2,
        extra_audio_filters: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcodes an input audio file to MP3 with specified parameters.
        Returns metadata about the generated file.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-i", str(input_path),
            "-vn",  # Disable video
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            "-ar", str(sample_rate),
            "-ac", str(channels),
        ]

        if extra_audio_filters:
            cmd.extend(["-af", extra_audio_filters])

        cmd.append(str(output_path))

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg transcode failed: {result.stderr}")

        file_size_bytes = output_path.stat().st_size
        duration_sec = self.get_duration(output_path)

        return {
            "output_path": str(output_path),
            "file_size_bytes": file_size_bytes,
            "file_size_kb": round(file_size_bytes / 1024, 2),
            "duration_sec": duration_sec,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels
        }

    def get_duration(self, audio_path: Path) -> float:
        """Retrieves audio duration in seconds using ffprobe/ffmpeg."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return float(res.stdout.strip())
        except Exception:
            pass

        # Fallback estimation using file size and bitrate
        return 0.0
