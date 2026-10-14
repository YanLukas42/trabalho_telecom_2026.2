"""Pipeline de diarização: prepara o áudio, envia o arquivo inteiro ao Gemini e exporta os relatórios."""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from telecom.audio.codecs import get_codec
from telecom.audio.ffmpeg import probe_duration
from telecom.audio.filters import WIDEBAND_VOICE
from telecom.audio.preparer import PreparedAudio, Treatment, prepare_audio
from telecom.audio.vad import SpeechMap
from telecom.diarization.alignment import TranscricaoWordLevel, write_word_alignment
from telecom.diarization.models import Diarizer, SpeakerSegment, Transcription
from telecom.diarization.report import RunStats, build_payload, render_markdown
from telecom.reporting import write_json
from telecom.settings import DIARIZATION_OUTPUT_DIR
from telecom.timefmt import format_range

logger = logging.getLogger(__name__)

# Bitrate fixo por codec: 16 kbps Opus VoIP ou 64 kbps MP3, ambos mono 16 kHz com passa-banda de voz.
BITRATE_BY_CODEC = {"opus": "16k", "mp3": "64k"}
PIPELINE_SAMPLE_RATE = 16000
PIPELINE_CHANNELS = 1


@dataclass(frozen=True)
class DiarizationOptions:
    codec: str = "opus"
    compact_silence: bool = False


@dataclass(frozen=True)
class DiarizationOutputs:
    payload: dict[str, Any]
    report_json: Path
    report_md: Path
    words_json: Path
    words: TranscricaoWordLevel


class DiarizationPipeline:
    """Orquestra as etapas. O diarizador é injetado, então o pipeline roda sem API em testes."""

    def __init__(
        self,
        diarizer: Diarizer,
        options: DiarizationOptions = DiarizationOptions(),
        output_dir: Path = DIARIZATION_OUTPUT_DIR,
    ):
        self._diarizer = diarizer
        self._options = options
        self._audio_dir = output_dir / "audio"
        self._reports_dir = output_dir / "reports"

    def run(self, source: Path) -> DiarizationOutputs:
        source = Path(source)
        started = time.perf_counter()
        original_duration = probe_duration(source)
        logger.info("Arquivo: %s (%.1fs)", source.name, original_duration)

        prepared = self._prepare(source)

        cloud_started = time.perf_counter()
        transcription = self._diarizer.diarize(prepared.path)
        cloud_elapsed = round(time.perf_counter() - cloud_started, 3)
        logger.info("Gemini respondeu em %.1fs com %d falas", cloud_elapsed, len(transcription.segments))

        segments = self._timeline(transcription.segments, prepared.speech_map)
        stats = self._stats(source, original_duration, prepared, transcription, started, cloud_elapsed)
        speech_dicts = prepared.speech_map.to_dicts() if prepared.speech_map else None
        payload = build_payload(stats, segments, speech_dicts)

        suffix = "_vad" if self._options.compact_silence else ""
        report_json = self._reports_dir / f"{source.stem}_diarizacao_pydantic{suffix}.json"
        report_md = self._reports_dir / f"{source.stem}_diarizacao_pydantic{suffix}.md"
        words_json = self._reports_dir / f"{source.stem}_palavra_por_palavra{suffix}.json"

        write_json(payload, report_json)
        report_md.parent.mkdir(parents=True, exist_ok=True)
        report_md.write_text(render_markdown(stats, segments), encoding="utf-8")
        words = write_word_alignment(report_json, words_json)

        logger.info("Relatórios: %s | %s | %s", report_json, report_md, words_json)
        return DiarizationOutputs(payload, report_json, report_md, words_json, words)

    def _prepare(self, source: Path) -> PreparedAudio:
        codec = get_codec(self._options.codec)
        tag = "_vad_compact" if self._options.compact_silence else "_optimized"
        treatment = Treatment(
            id=f"diarizacao{tag}",
            label="Pré-processamento para diarização",
            bitrate=BITRATE_BY_CODEC[codec.name],
            sample_rate=PIPELINE_SAMPLE_RATE,
            channels=PIPELINE_CHANNELS,
            codec=codec.name,
            filters=(WIDEBAND_VOICE,),
            compact_silence=self._options.compact_silence,
        )
        output = self._audio_dir / f"{source.stem}{tag}{codec.extension}"
        prepared = prepare_audio(source, output, treatment)
        logger.info("Áudio preparado em %.2fs (%.2f KB)", prepared.prep_time_sec, prepared.size_kb)
        if prepared.speech_map:
            logger.info(
                "VAD: %.1fs -> %.1fs (economia de %.2f%%)",
                prepared.speech_map.original_duration,
                prepared.speech_map.compact_duration,
                prepared.speech_map.saved_pct,
            )
        return prepared

    def _timeline(self, segments: tuple[SpeakerSegment, ...], speech_map: SpeechMap | None) -> list[dict[str, Any]]:
        """Com VAD, os tempos do áudio compactado são levados de volta à linha do tempo original."""
        timeline: list[dict[str, Any]] = []
        for segment in segments:
            start = round(segment.start_sec, 2)
            end = round(segment.end_sec, 2)
            item: dict[str, Any] = {
                "quemfala": segment.speaker,
                "textodefala": segment.text,
                "timestamp": format_range(start, end),
                "segundos_inicio": start,
                "segundos_fim": end,
            }
            if speech_map is not None:
                orig_start = speech_map.to_original(start)
                orig_end = max(orig_start, speech_map.to_original(end))
                item.update(
                    segundos_inicio_compact=start,
                    segundos_fim_compact=end,
                    segundos_inicio=orig_start,
                    segundos_fim=orig_end,
                    timestamp=format_range(orig_start, orig_end),
                )
            timeline.append(item)
        return timeline

    def _stats(
        self,
        source: Path,
        original_duration: float,
        prepared: PreparedAudio,
        transcription: Transcription,
        started: float,
        cloud_elapsed: float,
    ) -> RunStats:
        speech_map = prepared.speech_map
        return RunStats(
            file_name=source.name,
            codec=self._options.codec,
            original_duration_sec=original_duration,
            compact_duration_sec=speech_map.compact_duration if speech_map else original_duration,
            saved_sec=speech_map.saved_sec if speech_map else 0.0,
            saved_pct=speech_map.saved_pct if speech_map else 0.0,
            vad_applied=speech_map is not None,
            total_elapsed_sec=round(time.perf_counter() - started, 3),
            cloud_elapsed_sec=cloud_elapsed,
            prompt_tokens=transcription.prompt_tokens,
            candidate_tokens=transcription.candidate_tokens,
            total_tokens=transcription.total_tokens,
        )
