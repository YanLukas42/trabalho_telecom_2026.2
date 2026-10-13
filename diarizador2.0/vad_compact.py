"""
Voice Activity Detection (VAD) & Compactador de Áudio para Diarizador 2.0.
Remove pausas e silêncios mortos para economizar tokens na API do Gemini
e remapeia com exatidão matemática os timestamps para a linha do tempo original do vídeo.
"""

import subprocess
import time
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Garante inclusão de diretórios no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIARIZADOR_DIR = Path(__file__).resolve().parent

for p in [str(PROJECT_ROOT), str(DIARIZADOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def map_compact_to_original(t_compact: float, segments_map: List[Dict[str, float]]) -> float:
    """
    Mapeia um timestamp do áudio compactado (após remoção de silêncio por VAD)
    de volta para a linha do tempo original do arquivo de áudio/vídeo.

    segments_map = [
        {"orig_start": 10.0, "orig_end": 25.0, "comp_start": 0.0,  "comp_end": 15.0},
        {"orig_start": 40.0, "orig_end": 70.0, "comp_start": 15.0, "comp_end": 45.0},
        ...
    ]
    """
    if not segments_map:
        return t_compact

    for seg in segments_map:
        if seg["comp_start"] <= t_compact <= seg["comp_end"]:
            offset = t_compact - seg["comp_start"]
            return round(seg["orig_start"] + offset, 2)

    # Caso caia no último frame por arredondamento
    if segments_map and t_compact >= segments_map[-1]["comp_end"]:
        return segments_map[-1]["orig_end"]

    # Caso caia antes do primeiro bloco (arredondamento no início)
    if segments_map and t_compact < segments_map[0]["comp_start"]:
        return segments_map[0]["orig_start"]

    return t_compact


def format_seconds_to_timestamp(seconds: float) -> str:
    """Converte segundos float para formato HH:MM:SS ou MM:SS."""
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class VadAudioCompactor:
    """
    Detector de atividade de voz e compactador determinístico.
    Remove trechos sem fala e constrói a tabela de remapeamento temporal.
    """

    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        """Obtém duração exata do arquivo via ffprobe."""
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

    @staticmethod
    def detect_silence_intervals(
        audio_path: Path,
        noise_threshold_db: float = -35.0,
        min_silence_sec: float = 0.4
    ) -> List[Tuple[float, float]]:
        """
        Escaneia o arquivo com o filtro silencedetect do FFmpeg.
        Retorna lista de tuplas (silence_start, silence_end) em segundos.
        """
        cmd = [
            "ffmpeg",
            "-vn",
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
            match_start = re.search(r"silence_start:\s*([0-9.]+)", line)
            if match_start:
                silence_starts.append(float(match_start.group(1)))

            match_end = re.search(r"silence_end:\s*([0-9.]+)", line)
            if match_end:
                silence_ends.append(float(match_end.group(1)))

        intervals = []
        for i in range(min(len(silence_starts), len(silence_ends))):
            intervals.append((silence_starts[i], silence_ends[i]))

        return intervals

    @classmethod
    def build_speech_segments_map(
        cls,
        audio_path: Path,
        noise_threshold_db: float = -35.0,
        min_silence_sec: float = 0.4,
        pad_sec: float = 0.10
    ) -> Tuple[List[Dict[str, float]], float, float]:
        """
        Calcula os blocos de fala ativa e monta o mapa de correspondência
        entre o tempo original e o tempo compactado.
        """
        audio_path = Path(audio_path)
        duration = cls.get_audio_duration(audio_path)
        silences = cls.detect_silence_intervals(audio_path, noise_threshold_db, min_silence_sec)

        if not silences:
            segments_map = [{
                "orig_start": 0.0,
                "orig_end": round(duration, 3),
                "comp_start": 0.0,
                "comp_end": round(duration, 3),
                "duration": round(duration, 3)
            }]
            return segments_map, duration, duration

        # Identifica intervalos de fala entre as pausas de silêncio
        raw_speech = []
        if silences[0][0] > 0.05:
            raw_speech.append((0.0, silences[0][0]))

        for i in range(len(silences) - 1):
            sp_start = silences[i][1]
            sp_end = silences[i + 1][0]
            if sp_end - sp_start > 0.05:
                raw_speech.append((sp_start, sp_end))

        if silences[-1][1] < duration - 0.05:
            raw_speech.append((silences[-1][1], duration))

        # Aplica margem (padding) suave para proteger bordas de palavras e mescla colisões
        padded_speech = []
        for sp_start, sp_end in raw_speech:
            p_start = max(0.0, sp_start - pad_sec)
            p_end = min(duration, sp_end + pad_sec)

            if padded_speech and p_start <= padded_speech[-1][1]:
                prev_start, _ = padded_speech.pop()
                padded_speech.append((prev_start, max(p_end, padded_speech[-1][1] if padded_speech else p_end)))
            else:
                padded_speech.append((p_start, p_end))

        # Constrói o mapa de segmentos determinístico
        segments_map = []
        comp_pos = 0.0
        for orig_start, orig_end in padded_speech:
            seg_dur = round(orig_end - orig_start, 3)
            if seg_dur <= 0.05:
                continue
            comp_start = round(comp_pos, 3)
            comp_end = round(comp_pos + seg_dur, 3)
            segments_map.append({
                "orig_start": round(orig_start, 3),
                "orig_end": round(orig_end, 3),
                "comp_start": comp_start,
                "comp_end": comp_end,
                "duration": seg_dur
            })
            comp_pos = comp_end

        total_compact = round(comp_pos, 3)
        return segments_map, duration, total_compact

    @classmethod
    def compact_and_encode_audio(
        cls,
        input_path: Path,
        output_path: Path,
        segments_map: Optional[List[Dict[str, float]]] = None,
        codec: str = "opus",
        bitrate: str = "16k",
        sample_rate: int = 16000,
        channels: int = 1,
        filter_wideband: bool = True,
        noise_threshold_db: float = -35.0,
        min_silence_sec: float = 0.4,
        pad_sec: float = 0.10
    ) -> Dict[str, Any]:
        """
        Executa a compactação do áudio por VAD e codificação em Opus ou MP3:
        1. Gera o mapa de fala caso não tenha sido fornecido.
        2. Decodifica o áudio original em PCM bruto via pipe.
        3. Realiza o fatiamento de bytes na memória com precisão exata de amostras.
        4. Codifica o fluxo compactado com o codec alvo e filtro wideband.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        t0 = time.time()

        if segments_map is None:
            segments_map, orig_dur, comp_dur = cls.build_speech_segments_map(
                input_path,
                noise_threshold_db=noise_threshold_db,
                min_silence_sec=min_silence_sec,
                pad_sec=pad_sec
            )
        else:
            orig_dur = cls.get_audio_duration(input_path)
            comp_dur = segments_map[-1]["comp_end"] if segments_map else orig_dur

        bytes_per_sample = 2  # s16le = 16-bit
        frame_size = channels * bytes_per_sample

        # 1. Decodifica para raw PCM via FFmpeg
        cmd_decode = [
            "ffmpeg",
            "-y",
            "-vn",
            "-i", str(input_path),
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-"
        ]
        res_decode = subprocess.run(cmd_decode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_decode.returncode != 0:
            raise RuntimeError(f"Erro ao decodificar áudio para PCM: {res_decode.stderr.decode('utf-8', errors='replace')}")

        raw_pcm = res_decode.stdout

        # 2. Fatiamento em memória por byte chunks
        compact_byte_chunks = []
        for s in segments_map:
            byte_start = int(round(s["orig_start"] * sample_rate)) * frame_size
            byte_end = int(round(s["orig_end"] * sample_rate)) * frame_size
            byte_start = min(len(raw_pcm), max(0, byte_start))
            byte_end = min(len(raw_pcm), max(0, byte_end))
            compact_byte_chunks.append(raw_pcm[byte_start:byte_end])

        compact_bytes = b"".join(compact_byte_chunks) if compact_byte_chunks else raw_pcm

        # 3. Codifica fluxo compactado para Opus ou MP3
        cmd_encode = [
            "ffmpeg",
            "-y",
            "-f", "s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-i", "-"
        ]

        if filter_wideband:
            cmd_encode.extend(["-af", "highpass=f=80,lowpass=f=7500"])

        if codec.lower() == "opus":
            cmd_encode.extend([
                "-acodec", "libopus",
                "-b:a", bitrate,
                "-vbr", "on",
                "-application", "voip"
            ])
        else:
            cmd_encode.extend([
                "-acodec", "libmp3lame",
                "-b:a", bitrate
            ])

        cmd_encode.append(str(output_path))

        res_encode = subprocess.run(cmd_encode, input=compact_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        prep_time = round(time.time() - t0, 3)

        if res_encode.returncode != 0:
            raise RuntimeError(f"Erro ao codificar áudio compactado: {res_encode.stderr.decode('utf-8', errors='replace')}")

        size_bytes = output_path.stat().st_size
        silence_saved_sec = round(max(0.0, orig_dur - comp_dur), 2)
        silence_saved_pct = round((silence_saved_sec / orig_dur) * 100.0, 2) if orig_dur > 0 else 0.0

        return {
            "output_path": str(output_path),
            "file_size_bytes": size_bytes,
            "file_size_kb": round(size_bytes / 1024, 2),
            "prep_time_sec": prep_time,
            "original_duration_sec": round(orig_dur, 2),
            "compact_duration_sec": round(comp_dur, 2),
            "silence_saved_sec": silence_saved_sec,
            "silence_saved_pct": silence_saved_pct,
            "total_speech_segments": len(segments_map),
            "codec": codec,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels,
            "segments_map": segments_map
        }

    @classmethod
    def remap_diarized_segments(
        cls,
        segments: List[Dict[str, Any]],
        segments_map: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Aplica map_compact_to_original a todos os segmentos retornados pela IA,
        recalculando os segundos de início/fim e as strings de timestamp formatadas.
        """
        if not segments_map:
            return segments

        remapped = []
        for seg in segments:
            c_inicio = seg.get("segundos_inicio", 0.0)
            c_fim = seg.get("segundos_fim", 0.0)

            orig_inicio = map_compact_to_original(c_inicio, segments_map)
            orig_fim = map_compact_to_original(c_fim, segments_map)

            # Garante ordenação lógica de início e fim
            if orig_fim < orig_inicio:
                orig_fim = orig_inicio

            timestamp_str = f"{format_seconds_to_timestamp(orig_inicio)} - {format_seconds_to_timestamp(orig_fim)}"

            seg_copy = dict(seg)
            seg_copy["segundos_inicio"] = orig_inicio
            seg_copy["segundos_fim"] = orig_fim
            seg_copy["segundos_inicio_compact"] = c_inicio
            seg_copy["segundos_fim_compact"] = c_fim
            seg_copy["timestamp"] = timestamp_str

            remapped.append(seg_copy)

        return remapped
