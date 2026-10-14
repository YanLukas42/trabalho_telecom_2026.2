"""Alinhamento palavra a palavra: distribui o tempo de cada fala entre suas palavras, ponderado por fonética."""

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from telecom.timefmt import format_clock_ms

_VOWELS = frozenset("aeiouáéíóúâêîôûãõàü")
_WORD_CHARS = re.compile(r"[^\w]")


class PalavraTimestamp(BaseModel):
    palavra: str
    quemfala: str
    segundos_inicio: float
    segundos_fim: float
    timestamp: str


class TranscricaoWordLevel(BaseModel):
    arquivo: str
    total_palavras: int
    palavras: list[PalavraTimestamp]


def word_weight(word: str) -> float:
    """Peso relativo de uma palavra: letras, sílabas aproximadas (vogais) e pausa por pontuação."""
    clean = _WORD_CHARS.sub("", word.lower())
    if not clean:
        return 1.0
    vowels = sum(1 for char in clean if char in _VOWELS)
    weight = max(1.0, len(clean) * 0.7 + vowels * 0.8)
    if word.endswith((".", "?", "!")):
        weight += 1.8
    elif word.endswith((",", ";", ":", "...")):
        weight += 1.0
    return weight


def align_segment(segment: dict[str, Any]) -> list[PalavraTimestamp]:
    words = segment.get("textodefala", "").strip().split()
    if not words:
        return []

    speaker = segment.get("quemfala", "Falante")
    start = segment.get("segundos_inicio", 0.0)
    end = segment.get("segundos_fim", 0.0)
    span = max(0.2, end - start)

    weights = [word_weight(word) for word in words]
    total_weight = sum(weights)

    aligned: list[PalavraTimestamp] = []
    cursor = start
    for index, (word, weight) in enumerate(zip(words, weights)):
        word_start = round(cursor, 3)
        word_end = round(end, 3) if index == len(words) - 1 else round(cursor + weight / total_weight * span, 3)
        aligned.append(
            PalavraTimestamp(
                palavra=word,
                quemfala=speaker,
                segundos_inicio=word_start,
                segundos_fim=word_end,
                timestamp=f"{format_clock_ms(word_start)} - {format_clock_ms(word_end)}",
            )
        )
        cursor = word_end
    return aligned


def align_document(payload: dict[str, Any]) -> TranscricaoWordLevel:
    words = [word for segment in payload.get("segmentos", []) for word in align_segment(segment)]
    return TranscricaoWordLevel(
        arquivo=payload.get("arquivo", ""),
        total_palavras=len(words),
        palavras=words,
    )


def write_word_alignment(diarization_json: Path, output_json: Path) -> TranscricaoWordLevel:
    payload = json.loads(diarization_json.read_text(encoding="utf-8"))
    result = align_document(payload)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result
