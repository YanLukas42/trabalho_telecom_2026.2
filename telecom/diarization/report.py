"""Montagem do relatório de diarização (JSON e Markdown). Funções puras: recebem dados, devolvem texto ou dicionário."""

from dataclasses import dataclass
from typing import Any

from telecom.metrics.cost import estimate_cost


@dataclass(frozen=True)
class RunStats:
    """Números de uma execução, sem o conteúdo das falas."""

    file_name: str
    codec: str
    original_duration_sec: float
    compact_duration_sec: float
    saved_sec: float
    saved_pct: float
    vad_applied: bool
    total_elapsed_sec: float
    cloud_elapsed_sec: float
    prompt_tokens: int
    candidate_tokens: int
    total_tokens: int


def build_payload(
    stats: RunStats,
    segments: list[dict[str, Any]],
    speech_map: list[dict] | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cost = estimate_cost(stats.prompt_tokens, stats.candidate_tokens)
    payload: dict[str, Any] = {
        "arquivo": stats.file_name,
        "codec": stats.codec,
        "vad_aplicado": stats.vad_applied,
        "duracao_original_segundos": round(stats.original_duration_sec, 2),
        "duracao_compactada_segundos": round(stats.compact_duration_sec, 2),
        "economia_silencio_segundos": stats.saved_sec,
        "economia_silencio_pct": stats.saved_pct,
        "tempo_execucao_total_segundos": stats.total_elapsed_sec,
        "tempo_processamento_nuvem_segundos": stats.cloud_elapsed_sec,
        "metricas_tokens": {
            "prompt_tokens_audio": stats.prompt_tokens,
            "candidate_tokens_texto": stats.candidate_tokens,
            "total_tokens": stats.total_tokens,
        },
        "custo_estimado": {"custo_usd": cost.usd, "custo_brl": cost.brl},
        "total_turnos_fala": len(segments),
        "segmentos": segments,
    }
    if speech_map is not None:
        payload["vad_segments_map"] = speech_map
    payload.update(extra or {})
    return payload


def render_markdown(stats: RunStats, segments: list[dict[str, Any]]) -> str:
    cost = estimate_cost(stats.prompt_tokens, stats.candidate_tokens)
    title_suffix = " (com VAD)" if stats.vad_applied else ""
    lines = [
        f"# Transcrição Diarizada com Timestamps e Pydantic{title_suffix}",
        "",
        f"- **Arquivo:** `{stats.file_name}`",
        f"- **Duração Original do Áudio:** `{round(stats.original_duration_sec / 60, 2)} min` ({round(stats.original_duration_sec, 1)}s)",
    ]
    if stats.vad_applied:
        lines.append(
            f"- **Duração Compactada (VAD):** `{round(stats.compact_duration_sec / 60, 2)} min` "
            f"({round(stats.compact_duration_sec, 1)}s) — Economia de `{stats.saved_pct}%` ({round(stats.saved_sec, 1)}s)"
        )
    lines += [
        f"- **Tempo Total de Execução:** `{stats.total_elapsed_sec}s` ({round(stats.total_elapsed_sec / 60, 2)} min)",
        f"- **Tokens Utilizados:** `{stats.total_tokens:,}` (Entrada: `{stats.prompt_tokens:,}`, Saída: `{stats.candidate_tokens:,}`)",
        f"- **Custo Estimado:** `US$ {cost.usd}` (~ `R$ {cost.brl}`)",
        f"- **Total de Turnos de Fala:** `{len(segments)}`",
        "",
        "---",
        "",
    ]
    for seg in segments:
        identified = seg.get("falante_identificado")
        name = f"{identified} ({seg['quemfala']})" if identified else seg["quemfala"]
        lines.append(f"**[{seg['timestamp']}] {name}:**")
        lines.append(f"> {seg['textodefala']}")
        lines.append("")
    return "\n".join(lines)
