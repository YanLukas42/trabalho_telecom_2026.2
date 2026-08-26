"""
Accuracy evaluation metrics: Word Error Rate (WER) and Character Error Rate (CER).
Includes robust text normalization (punctuation stripping, case insensitivity, whitespace cleaning).
"""

import re
import unicodedata
from typing import Dict, Any, Tuple


class TextNormalizer:
    """Normalizes speech transcription text for consistent ASR evaluation."""

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove accents/diacritics for phonetic fairness (optional, can be toggled)
        # We preserve accents in standard Portuguese evaluation, but normalize spacing and punctuation
        # Normalize unicode NFKC
        text = unicodedata.normalize("NFKC", text)
        # Remove all punctuation and symbols except letters and numbers
        text = re.sub(r"[^\w\s]", " ", text)
        # Collapse multiple spaces into one
        text = re.sub(r"\s+", " ", text).strip()
        return text


class AccuracyEvaluator:
    """Calculates WER, CER, and Levenshtein distances between Ground Truth and Hypothesis."""

    @staticmethod
    def levenshtein_distance(seq1: list, seq2: list) -> int:
        """Standard dynamic programming Levenshtein distance."""
        size_x = len(seq1) + 1
        size_y = len(seq2) + 1
        matrix = [[0] * size_y for _ in range(size_x)]

        for x in range(size_x):
            matrix[x][0] = x
        for y in range(size_y):
            matrix[0][y] = y

        for x in range(1, size_x):
            for y in range(1, size_y):
                if seq1[x - 1] == seq2[y - 1]:
                    matrix[x][y] = matrix[x - 1][y - 1]
                else:
                    matrix[x][y] = min(
                        matrix[x - 1][y] + 1,      # Deletion
                        matrix[x][y - 1] + 1,      # Insertion
                        matrix[x - 1][y - 1] + 1   # Substitution
                    )
        return matrix[size_x - 1][size_y - 1]

    @classmethod
    def calculate_wer(cls, reference: str, hypothesis: str) -> float:
        """
        Word Error Rate (WER) = (S + D + I) / N
        Returns percentage between 0.0% and 100.0%+
        """
        norm_ref = TextNormalizer.normalize(reference)
        norm_hyp = TextNormalizer.normalize(hypothesis)

        ref_words = norm_ref.split()
        hyp_words = norm_hyp.split()

        if not ref_words:
            return 0.0 if not hyp_words else 100.0

        distance = cls.levenshtein_distance(ref_words, hyp_words)
        wer = (distance / len(ref_words)) * 100.0
        return round(wer, 2)

    @classmethod
    def calculate_cer(cls, reference: str, hypothesis: str) -> float:
        """
        Character Error Rate (CER) = Levenshtein(chars) / Total chars in reference.
        """
        norm_ref = TextNormalizer.normalize(reference)
        norm_hyp = TextNormalizer.normalize(hypothesis)

        ref_chars = list(norm_ref.replace(" ", ""))
        hyp_chars = list(norm_hyp.replace(" ", ""))

        if not ref_chars:
            return 0.0 if not hyp_chars else 100.0

        distance = cls.levenshtein_distance(ref_chars, hyp_chars)
        cer = (distance / len(ref_chars)) * 100.0
        return round(cer, 2)

    @classmethod
    def evaluate(cls, reference: str, hypothesis: str) -> Dict[str, Any]:
        """Calculates full accuracy report."""
        wer = cls.calculate_wer(reference, hypothesis)
        cer = cls.calculate_cer(reference, hypothesis)
        return {
            "wer": wer,
            "cer": cer,
            "accuracy_word_pct": max(0.0, round(100.0 - wer, 2)),
            "normalized_reference": TextNormalizer.normalize(reference),
            "normalized_hypothesis": TextNormalizer.normalize(hypothesis),
        }
