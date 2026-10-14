"""Motor de benchmark: aplica cada tratamento, transcreve e compara com a referência."""

import logging
from pathlib import Path
from typing import Any, Protocol, Sequence

from telecom.asr.gemini import GeminiClient, GenerationResult
from telecom.audio.codecs import get_codec, mime_type_for_path
from telecom.audio.preparer import PreparedAudio, Treatment, prepare_audio
from telecom.metrics import text
from telecom.metrics.cost import compression_stats, estimate_cost

logger = logging.getLogger(__name__)


class AudioTranscriber(Protocol):
    def transcribe(self, audio_path: Path) -> GenerationResult: ...


class GeminiAudioTranscriber:
    """Transcrição de um arquivo de áudio com um prompt fixo."""

    def __init__(self, client: GeminiClient, prompt: str):
        self._client = client
        self._prompt = prompt

    def transcribe(self, audio_path: Path) -> GenerationResult:
        return self._client.generate(
            audio=audio_path.read_bytes(),
            mime_type=mime_type_for_path(audio_path),
            prompt=self._prompt,
        )


class BenchmarkEngine:
    """Para cada tratamento: prepara o áudio, transcreve (se houver transcritor) e mede.

    A referência de WER/CER é o texto informado (ex.: ground truth) ou, na falta dele,
    a transcrição do tratamento marcado como `is_baseline`.
    """

    def __init__(
        self,
        treatments: Sequence[Treatment],
        output_dir: Path,
        transcriber: AudioTranscriber | None = None,
        reference: str | None = None,
        strip_speaker_labels: bool = False,
    ):
        self._treatments = list(treatments)
        self._output_dir = output_dir
        self._transcriber = transcriber
        self._reference = reference
        self._strip_labels = strip_speaker_labels

    def run(self, source: Path) -> list[dict[str, Any]]:
        source = Path(source)
        original_bytes = source.stat().st_size
        rows: list[dict[str, Any]] = []

        for treatment in self._treatments:
            logger.info("[%s] %s", treatment.category, treatment.label)
            output = self._output_dir / f"{source.stem}_{treatment.id}{get_codec(treatment.codec).extension}"
            prepared = prepare_audio(source, output, treatment)
            rows.append(self._measure(source, treatment, prepared, original_bytes))

        self._score(rows)
        return rows

    def _measure(self, source: Path, treatment: Treatment, prepared: PreparedAudio, original_bytes: int) -> dict[str, Any]:
        ratio, saved_pct = compression_stats(original_bytes, prepared.size_bytes)
        row: dict[str, Any] = {
            "sample_file": source.name,
            "treatment_id": treatment.id,
            "treatment_label": treatment.label,
            "category": treatment.category,
            "codec": treatment.codec,
            "bitrate": treatment.bitrate,
            "sample_rate": treatment.sample_rate,
            "channels": treatment.channels,
            "compact_silence": treatment.compact_silence,
            "original_size_kb": round(original_bytes / 1024, 2),
            "processed_size_kb": prepared.size_kb,
            "compression_ratio": ratio,
            "bandwidth_saved_pct": saved_pct,
            "prep_time_sec": prepared.prep_time_sec,
            "transcript": "",
            "error": "",
            "api_latency_sec": 0.0,
            "prompt_tokens": 0,
            "candidate_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "estimated_cost_brl": 0.0,
            "speaker_turns": 0,
            "wer": None,
            "cer": None,
            "is_baseline": treatment.is_baseline,
        }

        if self._transcriber is None:
            return row

        try:
            result = self._transcriber.transcribe(prepared.path)
        except Exception as exc:
            logger.error("Falha na API em %s: %s", treatment.id, exc)
            row["error"] = str(exc)
            return row

        cost = estimate_cost(result.prompt_tokens, result.candidate_tokens)
        row.update(
            transcript=result.text,
            api_latency_sec=result.latency_sec,
            prompt_tokens=result.prompt_tokens,
            candidate_tokens=result.candidate_tokens,
            total_tokens=result.total_tokens,
            estimated_cost_usd=cost.usd,
            estimated_cost_brl=cost.brl,
            speaker_turns=text.count_speaker_turns(result.text),
        )
        return row

    def _score(self, rows: list[dict[str, Any]]) -> None:
        reference = self._reference
        if reference is None:
            reference = next((row["transcript"] for row in rows if row["is_baseline"] and row["transcript"]), None)
        if not reference:
            return
        for row in rows:
            if row["transcript"]:
                row["wer"] = text.wer(reference, row["transcript"], self._strip_labels)
                row["cer"] = text.cer(reference, row["transcript"])
