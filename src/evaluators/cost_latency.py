"""
Cost, Latency, and Telecom Transmission Evaluator.
Measures token counts, bandwidth savings, compression ratios, and estimated financial costs.
"""

from typing import Dict, Any
from config import PRICING_PER_1M_INPUT_TOKENS, PRICING_PER_1M_OUTPUT_TOKENS, USD_TO_BRL


class CostLatencyEvaluator:
    """Computes efficiency metrics for audio processing and AI inference."""

    @staticmethod
    def calculate_compression_stats(original_bytes: int, processed_bytes: int) -> Dict[str, Any]:
        """Calculates payload compression ratio and percentage saved."""
        if original_bytes <= 0:
            return {"compression_ratio": 1.0, "bandwidth_saved_pct": 0.0}

        ratio = round(original_bytes / max(1, processed_bytes), 2)
        saved_pct = round(((original_bytes - processed_bytes) / original_bytes) * 100.0, 2)
        return {
            "compression_ratio": ratio,
            "bandwidth_saved_pct": saved_pct
        }

    @staticmethod
    def estimate_cost(prompt_tokens: int, candidate_tokens: int) -> Dict[str, float]:
        """
        Estimates API cost in USD and BRL for the transaction based on Gemini Flash pricing.
        """
        cost_input_usd = (prompt_tokens / 1_000_000.0) * PRICING_PER_1M_INPUT_TOKENS
        cost_output_usd = (candidate_tokens / 1_000_000.0) * PRICING_PER_1M_OUTPUT_TOKENS
        total_usd = cost_input_usd + cost_output_usd
        total_brl = total_usd * USD_TO_BRL

        return {
            "cost_input_usd": cost_input_usd,
            "cost_output_usd": cost_output_usd,
            "total_cost_usd": round(total_usd, 6),
            "total_cost_brl": round(total_brl, 6)
        }
