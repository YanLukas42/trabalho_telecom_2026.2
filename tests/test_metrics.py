"""
Unit tests for accuracy metrics, text normalization, and cost calculations.
"""

from src.evaluators.accuracy import TextNormalizer, AccuracyEvaluator
from src.evaluators.cost_latency import CostLatencyEvaluator


def test_text_normalization():
    raw = "Olá, Mundo! Este é um TESTE... com pontuação."
    norm = TextNormalizer.normalize(raw)
    assert norm == "olá mundo este é um teste com pontuação"


def test_perfect_wer_cer():
    ref = "engenharia de telecomunicações é incrível"
    hyp = "engenharia de telecomunicações é incrível"
    acc = AccuracyEvaluator.evaluate(ref, hyp)
    assert acc["wer"] == 0.0
    assert acc["cer"] == 0.0
    assert acc["accuracy_word_pct"] == 100.0


def test_wer_with_errors():
    ref = "o áudio foi transmitido com sucesso"
    hyp = "o áudio foi enviado com sucesso"
    acc = AccuracyEvaluator.evaluate(ref, hyp)
    # 1 substitution out of 6 words => 1/6 ~ 16.67%
    assert acc["wer"] == 16.67


def test_compression_calculation():
    stats = CostLatencyEvaluator.calculate_compression_stats(1000, 200)
    assert stats["compression_ratio"] == 5.0
    assert stats["bandwidth_saved_pct"] == 80.0
