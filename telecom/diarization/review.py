"""Revisão por IA sobre o texto: sugere o nome dos falantes e aponta possíveis erros de transcrição.

A IA não ouve o áudio. Ela trabalha só com o texto, então:
- um nome só entra se o trecho que o justifica existir literalmente na transcrição;
- uma revisão só entra se o trecho citado estiver na fala indicada;
- correções são sugestões: o texto original nunca é alterado.
"""

import json
import logging
from dataclasses import dataclass
from typing import Protocol, Sequence

from pydantic import BaseModel, Field, ValidationError

from telecom.asr.gemini import GeminiClient
from telecom.diarization.models import SpeakerSegment
from telecom.metrics.text import normalize

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 0.7
REVIEW_TEMPERATURE = 0.1
REVIEW_MAX_OUTPUT_TOKENS = 16_384
REVIEW_MAX_RETRIES = 4


class FalanteIdentificado(BaseModel):
    rotulo: str = Field(description="Rótulo do falante na transcrição, ex.: SPEAKER_00")
    nome: str = Field(description="Nome ou papel citado no próprio texto; vazio se o texto não indica")
    confianca: float = Field(description="Confiança de 0 a 1 de que o nome corresponde ao rótulo")
    evidencia: str = Field(description="Trecho literal do texto que justifica o nome; vazio se não há")


class RevisaoFala(BaseModel):
    indice_fala: int = Field(description="Número da fala, indicado entre colchetes na transcrição")
    tipo: str = Field(description="'legenda' (erro de transcrição), 'nome' (grafia de nome próprio) ou 'sentido' (trecho incoerente)")
    trecho: str = Field(description="Trecho exato, como aparece na fala")
    sugestao: str = Field(description="Correção sugerida; não é aplicada automaticamente")
    motivo: str = Field(description="Por que o trecho parece errado")


class RevisaoTranscricao(BaseModel):
    falantes: list[FalanteIdentificado] = Field(description="Uma entrada por rótulo de falante")
    revisoes: list[RevisaoFala] = Field(description="Possíveis erros; lista vazia se nenhum")


@dataclass(frozen=True)
class AppliedReview:
    names: dict[str, str]
    falantes: list[dict]
    revisoes: list[dict]


_PROMPT_HEADER = (
    "Você revisa uma transcrição feita por reconhecimento automático de fala. "
    "Os falantes têm rótulos anônimos (SPEAKER_00, etc.). Você NÃO ouve o áudio: trabalhe apenas com o texto abaixo.\n\n"
    "Tarefas:\n"
    "1. Para cada rótulo, diga o nome ou papel da pessoa somente se o próprio texto indicar "
    "(apresentação, vocativo como 'doutor X', 'senhora Y'). Não invente nomes. "
    "Dê uma confiança de 0 a 1 e copie em 'evidencia' o trecho literal que sustenta a conclusão. "
    "Se o texto não indicar, deixe o nome vazio.\n"
    "2. Aponte possíveis erros de transcrição: palavras sem sentido no contexto, nomes próprios grafados de forma "
    "inconsistente, números improváveis. Indique o número da fala, o trecho exato, a sugestão e o motivo. "
    "Não reescreva o texto.\n\n"
    "Transcrição:\n"
)


def build_review_prompt(segments: Sequence[SpeakerSegment]) -> str:
    lines = "\n".join(f"[{index}] {segment.speaker}: {segment.text}" for index, segment in enumerate(segments))
    return _PROMPT_HEADER + lines


def parse_review(raw_text: str) -> RevisaoTranscricao:
    try:
        return RevisaoTranscricao.model_validate(json.loads(raw_text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Revisão do Gemini inválida: {exc}") from exc


def identified_names(review: RevisaoTranscricao, segments: Sequence[SpeakerSegment]) -> dict[str, str]:
    """Nome por rótulo, só com confiança mínima e evidência literal presente no texto."""
    corpus = normalize(" ".join(segment.text for segment in segments))
    names: dict[str, str] = {}
    for item in review.falantes:
        name = item.nome.strip()
        if not name:
            continue
        if item.confianca < MIN_CONFIDENCE:
            logger.info("Nome descartado (confiança %.2f): %s -> %s", item.confianca, item.rotulo, name)
            continue
        evidence = normalize(item.evidencia)
        if not evidence or evidence not in corpus:
            logger.info("Nome descartado (evidência ausente no texto): %s -> %s", item.rotulo, name)
            continue
        names[item.rotulo] = name
    return names


def valid_reviews(review: RevisaoTranscricao, segments: Sequence[SpeakerSegment]) -> list[RevisaoFala]:
    kept: list[RevisaoFala] = []
    for item in review.revisoes:
        in_range = 0 <= item.indice_fala < len(segments)
        if in_range and item.trecho and item.trecho in segments[item.indice_fala].text:
            kept.append(item)
        else:
            logger.info("Revisão descartada (trecho não encontrado na fala %d)", item.indice_fala)
    return kept


def apply_review(review: RevisaoTranscricao, segments: Sequence[SpeakerSegment]) -> AppliedReview:
    return AppliedReview(
        names=identified_names(review, segments),
        falantes=[item.model_dump() for item in review.falantes],
        revisoes=[item.model_dump() for item in valid_reviews(review, segments)],
    )


class TranscriptReviewer(Protocol):
    def review(self, segments: Sequence[SpeakerSegment]) -> RevisaoTranscricao: ...


class GeminiReviewer:
    """Revisão com Gemini, só texto. Não envia áudio."""

    def __init__(self, client: GeminiClient):
        self._client = client

    def review(self, segments: Sequence[SpeakerSegment]) -> RevisaoTranscricao:
        result = self._client.generate_text(
            build_review_prompt(segments),
            response_schema=RevisaoTranscricao,
            temperature=REVIEW_TEMPERATURE,
            max_output_tokens=REVIEW_MAX_OUTPUT_TOKENS,
            max_retries=REVIEW_MAX_RETRIES,
        )
        logger.info("Revisão por IA: %d tokens", result.total_tokens)
        return parse_review(result.text)
