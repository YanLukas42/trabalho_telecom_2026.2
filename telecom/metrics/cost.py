"""Métricas de custo e de compressão de banda."""

from dataclasses import dataclass

from telecom import settings


@dataclass(frozen=True)
class Cost:
    usd: float
    brl: float


def estimate_cost(prompt_tokens: int, candidate_tokens: int) -> Cost:
    usd = (
        prompt_tokens / 1_000_000 * settings.PRICE_INPUT_USD_PER_M
        + candidate_tokens / 1_000_000 * settings.PRICE_OUTPUT_USD_PER_M
    )
    return Cost(usd=round(usd, 6), brl=round(usd * settings.USD_TO_BRL, 6))


def compression_stats(original_bytes: int, processed_bytes: int) -> tuple[float, float]:
    """(razão de compressão, porcentagem de banda economizada)."""
    if original_bytes <= 0:
        return 1.0, 0.0
    ratio = round(original_bytes / max(1, processed_bytes), 2)
    saved_pct = round((original_bytes - processed_bytes) / original_bytes * 100.0, 2)
    return ratio, saved_pct
