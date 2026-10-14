import pytest

from telecom.metrics import text
from telecom.metrics.cost import compression_stats, estimate_cost


def test_normalize_strips_case_and_punctuation():
    assert text.normalize("Olá, Mundo! Este é um TESTE... com pontuação.") == "olá mundo este é um teste com pontuação"


def test_normalize_can_strip_speaker_labels():
    assert text.normalize("[Juiz] Bom dia.", strip_speaker_labels=True) == "bom dia"


def test_wer_perfect_and_with_one_substitution():
    assert text.wer("engenharia de telecomunicações", "engenharia de telecomunicações") == 0.0
    assert text.wer("o áudio foi transmitido com sucesso", "o áudio foi enviado com sucesso") == 16.67


def test_cer_counts_characters_without_spaces():
    assert text.cer("abcd", "abce") == 25.0


def test_empty_reference_is_handled():
    assert text.wer("", "") == 0.0
    assert text.wer("", "algo") == 100.0


def test_count_speaker_turns_prefers_labels_then_paragraphs():
    assert text.count_speaker_turns("[Juiz] oi\n[Réu] tudo bem") == 2
    assert text.count_speaker_turns("primeiro\n\nsegundo") == 2
    assert text.count_speaker_turns("") == 0


def test_estimate_cost_uses_gemini_flash_prices():
    cost = estimate_cost(1_000_000, 1_000_000)
    assert cost.usd == pytest.approx(0.75)
    assert cost.brl == pytest.approx(0.75 * 5.70)


def test_compression_stats():
    assert compression_stats(1000, 200) == (5.0, 80.0)
    assert compression_stats(0, 10) == (1.0, 0.0)
