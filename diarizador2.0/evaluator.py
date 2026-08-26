"""
Avaliador de Diarização e Desvio Textual (WER/CER vs. Baseline 320k).
"""

import re
import unicodedata
from typing import Dict, Any, List


class DiarizationEvaluator:
    """Calcula desvio de palavras/caracteres e métricas de turnos de falantes."""

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        # Remove rótulos de falantes como [Juiz], [Réu] para calcular WER textual puro
        text = re.sub(r"\[.*?\]", " ", text)
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def count_speaker_turns(text: str) -> int:
        """Conta quantos turnos de fala delimitados por [] ou parágrafos existem."""
        if not text:
            return 0
        matches = re.findall(r"\[(.*?)\]", text)
        return len(matches) if matches else len([p for p in text.split("\n\n") if p.strip()])

    @classmethod
    def calculate_wer(cls, reference: str, hypothesis: str) -> float:
        norm_ref = cls.normalize_text(reference)
        norm_hyp = cls.normalize_text(hypothesis)

        ref_words = norm_ref.split()
        hyp_words = norm_hyp.split()

        if not ref_words:
            return 0.0 if not hyp_words else 100.0

        size_x = len(ref_words) + 1
        size_y = len(hyp_words) + 1
        matrix = [[0] * size_y for _ in range(size_x)]

        for x in range(size_x):
            matrix[x][0] = x
        for y in range(size_y):
            matrix[0][y] = y

        for x in range(1, size_x):
            for y in range(1, size_y):
                if ref_words[x - 1] == hyp_words[y - 1]:
                    matrix[x][y] = matrix[x - 1][y - 1]
                else:
                    matrix[x][y] = min(
                        matrix[x - 1][y] + 1,
                        matrix[x][y - 1] + 1,
                        matrix[x - 1][y - 1] + 1
                    )

        distance = matrix[size_x - 1][size_y - 1]
        return round((distance / len(ref_words)) * 100.0, 2)
