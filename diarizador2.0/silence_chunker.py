"""
Silence-Aware Audio Chunker (Fatiamento Inteligente em Pausas).
Detecta silêncios naturais usando FFmpeg silencedetect e fatia o áudio sem cortar palavras.
"""

import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


class SilenceAwareChunker:
    """Fatia áudios longos estritamente em momentos de silêncio/pausas de respiração."""

    @staticmethod
    def detect_silence_intervals(
        audio_path: Path,
        noise_threshold_db: float = -35.0,
        min_silence_sec: float = 0.3
    ) -> List[Tuple[float, float]]:
        """
        Escaneia o arquivo de áudio com o filtro silencedetect do FFmpeg.
        Retorna uma lista de tuplas (inicio_silencio, fim_silencio) em segundos.
        """
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_silence_sec}",
            "-f", "null",
            "-"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr_output = res.stderr

        silence_starts = []
        silence_ends = []

        for line in stderr_output.splitlines():
            # Procura linhas do tipo: [silencedetect @ ...] silence_start: 124.521
            match_start = re.search(r"silence_start:\s*([0-9.]+)", line)
            if match_start:
                silence_starts.append(float(match_start.group(1)))

            # Procura linhas do tipo: [silencedetect @ ...] silence_end: 125.104
            match_end = re.search(r"silence_end:\s*([0-9.]+)", line)
            if match_end:
                silence_ends.append(float(match_end.group(1)))

        intervals = []
        for i in range(min(len(silence_starts), len(silence_ends))):
            intervals.append((silence_starts[i], silence_ends[i]))

        return intervals

    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        """Obtém duração exata do áudio via ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    @classmethod
    def calculate_cut_points(
        cls,
        audio_path: Path,
        target_chunk_sec: float = 90.0,
        search_window_sec: float = 18.0
    ) -> List[float]:
        """
        Calcula os pontos de corte ideais onde ninguém está falando.
        """
        duration = cls.get_audio_duration(audio_path)
        if duration <= target_chunk_sec * 1.2:
            # Áudio curto: não precisa fatiar
            return [0.0, duration]

        silences = cls.detect_silence_intervals(audio_path)
        cut_points = [0.0]
        current_pos = 0.0

        while current_pos + target_chunk_sec < duration:
            target_cut = current_pos + target_chunk_sec
            min_bound = target_cut - search_window_sec
            max_bound = target_cut + search_window_sec

            # Encontrar pausas dentro da janela de busca
            candidate_silences = [
                (s_start, s_end) for (s_start, s_end) in silences
                if min_bound <= s_start <= max_bound or min_bound <= s_end <= max_bound
            ]

            if candidate_silences:
                # Escolhe a pausa mais longa mais próxima do alvo
                best_silence = max(candidate_silences, key=lambda s: s[1] - s[0])
                # Corta no ponto médio do silêncio
                cut_time = round((best_silence[0] + best_silence[1]) / 2.0, 3)
            else:
                # Fallback se não achar silêncio estrito: corta no target_cut
                cut_time = round(target_cut, 3)

            cut_points.append(cut_time)
            current_pos = cut_time

        if cut_points[-1] < duration:
            cut_points.append(duration)

        return cut_points

    @classmethod
    def slice_audio(
        cls,
        audio_path: Path,
        output_dir: Path,
        target_chunk_sec: float = 120.0
    ) -> List[Dict[str, Any]]:
        """
        Fatia o áudio em arquivos MP3 físicos alinhados aos silêncios.
        Retorna metadados de cada bloco (caminho, start_sec, end_sec, duracao).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cut_points = cls.calculate_cut_points(audio_path, target_chunk_sec=target_chunk_sec)
        chunks_meta = []

        stem = audio_path.stem
        ext = audio_path.suffix or ".opus"
        for i in range(len(cut_points) - 1):
            t_start = cut_points[i]
            t_end = cut_points[i + 1]
            chunk_duration = t_end - t_start

            chunk_filename = f"{stem}_chunk_{i+1:03d}{ext}"
            chunk_path = output_dir / chunk_filename

            # Extração rápida com FFmpeg (-ss antes do -i para seek rápido e -to)
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(t_start),
                "-to", str(t_end),
                "-i", str(audio_path),
                "-acodec", "copy",  # Cópia direta de stream sem recodificar (instantâneo!)
                str(chunk_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            chunks_meta.append({
                "chunk_index": i + 1,
                "chunk_path": str(chunk_path),
                "start_sec": t_start,
                "end_sec": t_end,
                "duration_sec": round(chunk_duration, 2)
            })

        return chunks_meta
