"""Métricas textuais para comparar transcrições: WER e CER (distância de Levenshtein)."""

import re
import unicodedata
from typing import Sequence, TypeVar

_T = TypeVar("_T")
_SPEAKER_LABEL = re.compile(r"\[.*?\]")


def normalize(text: str, strip_speaker_labels: bool = False) -> str:
    """Minúsculas, sem pontuação e com espaços colapsados.

    `strip_speaker_labels` remove rótulos como [Juiz] antes da comparação, para medir só o texto falado.
    """
    if not text:
        return ""
    text = text.lower()
    if strip_speaker_labels:
        text = _SPEAKER_LABEL.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def levenshtein(seq_a: Sequence[_T], seq_b: Sequence[_T]) -> int:
    """Distância de edição (substituição, inserção e remoção custam 1)."""
    previous = list(range(len(seq_b) + 1))
    for i, item_a in enumerate(seq_a, start=1):
        current = [i] + [0] * len(seq_b)
        for j, item_b in enumerate(seq_b, start=1):
            cost = 0 if item_a == item_b else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
        previous = current
    return previous[-1]


def wer(reference: str, hypothesis: str, strip_speaker_labels: bool = False) -> float:
    """Word Error Rate em porcentagem: (substituições + inserções + remoções) / palavras da referência."""
    ref_words = normalize(reference, strip_speaker_labels).split()
    hyp_words = normalize(hypothesis, strip_speaker_labels).split()
    if not ref_words:
        return 0.0 if not hyp_words else 100.0
    return round(levenshtein(ref_words, hyp_words) / len(ref_words) * 100.0, 2)


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate em porcentagem, ignorando espaços."""
    ref_chars = list(normalize(reference).replace(" ", ""))
    hyp_chars = list(normalize(hypothesis).replace(" ", ""))
    if not ref_chars:
        return 0.0 if not hyp_chars else 100.0
    return round(levenshtein(ref_chars, hyp_chars) / len(ref_chars) * 100.0, 2)


def count_speaker_turns(text: str) -> int:
    """Turnos de fala: rótulos entre colchetes, ou parágrafos quando não há rótulos."""
    if not text:
        return 0
    labels = re.findall(r"\[(.*?)\]", text)
    if labels:
        return len(labels)
    return len([paragraph for paragraph in text.split("\n\n") if paragraph.strip()])
