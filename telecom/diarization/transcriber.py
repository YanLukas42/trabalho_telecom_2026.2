"""Diarização com o Gemini: o áudio inteiro vai numa chamada, e a resposta segue o esquema Pydantic."""

from pathlib import Path

from pydantic import ValidationError

from telecom.asr.gemini import GeminiClient
from telecom.asr.repair import parse_chunk_json
from telecom.asr.schemas import TranscricaoChunkDiarizada
from telecom.audio.codecs import mime_type_for_path
from telecom.diarization.models import SpeakerSegment, Transcription
from telecom.diarization.prompts import build_diarization_prompt

TEMPERATURE = 0.1
# Teto de saída do Gemini 2.5 Flash. Uma transcrição longa precisa de todo esse espaço.
MAX_OUTPUT_TOKENS = 65_536
# A API recusa requisições com dados inline acima de 20 MB.
INLINE_AUDIO_LIMIT_BYTES = 20 * 1024 * 1024
MAX_RETRIES = 4


class GeminiDiarizer:
    def __init__(self, client: GeminiClient, max_retries: int = MAX_RETRIES):
        self._client = client
        self._max_retries = max_retries

    def diarize(self, audio_path: Path) -> Transcription:
        audio = audio_path.read_bytes()
        if len(audio) > INLINE_AUDIO_LIMIT_BYTES:
            raise ValueError(
                f"{audio_path.name} tem {len(audio) / 2**20:.1f} MB; o limite inline da API é 20 MB. "
                "Use --codec opus (16 kbps) ou um arquivo menor."
            )

        result = self._client.generate(
            audio=audio,
            mime_type=mime_type_for_path(audio_path),
            prompt=build_diarization_prompt(),
            response_schema=TranscricaoChunkDiarizada,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            max_retries=self._max_retries,
        )
        return Transcription(
            segments=_parse_segments(result.text),
            prompt_tokens=result.prompt_tokens,
            candidate_tokens=result.candidate_tokens,
            total_tokens=result.total_tokens,
            latency_sec=result.latency_sec,
        )


def _parse_segments(raw_text: str) -> tuple[SpeakerSegment, ...]:
    data = parse_chunk_json(raw_text or "{}")
    if data is None:
        raise ValueError("A resposta do Gemini não é JSON válido, nem após o reparo.")
    try:
        parsed = TranscricaoChunkDiarizada.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"A resposta do Gemini está fora do esquema: {exc}") from exc
    return tuple(
        SpeakerSegment(
            speaker=seg.quemfala,
            text=seg.textodefala,
            start_sec=seg.segundos_inicio,
            end_sec=seg.segundos_fim,
        )
        for seg in parsed.segmentos
    )
