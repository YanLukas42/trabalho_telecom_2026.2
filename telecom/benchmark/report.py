"""Relatórios do benchmark: CSV com todas as colunas, JSON e um resumo em Markdown."""

from pathlib import Path
from typing import Any, Sequence

from telecom.reporting import markdown_table, write_csv, write_json

SUMMARY_COLUMNS = (
    "treatment_label",
    "processed_size_kb",
    "bandwidth_saved_pct",
    "wer",
    "cer",
    "speaker_turns",
    "total_tokens",
    "api_latency_sec",
    "estimated_cost_usd",
)


def write_benchmark_reports(rows: Sequence[dict[str, Any]], source: Path, reports_dir: Path) -> dict[str, Path]:
    stem = f"{source.stem}_benchmark"
    paths = {
        "csv": reports_dir / f"{stem}.csv",
        "json": reports_dir / f"{stem}.json",
        "md": reports_dir / f"{stem}.md",
    }
    write_csv(rows, paths["csv"])
    write_json(list(rows), paths["json"])
    paths["md"].parent.mkdir(parents=True, exist_ok=True)
    paths["md"].write_text(_render(rows, source), encoding="utf-8")
    return paths


def _render(rows: Sequence[dict[str, Any]], source: Path) -> str:
    lines = [
        f"# Benchmark de tratamentos: `{source.name}`",
        "",
        f"Experimentos executados: **{len(rows)}**",
        "",
        markdown_table(rows, SUMMARY_COLUMNS),
        "",
        "## Transcrições",
        "",
    ]
    for row in rows:
        lines.append(f"### {row['treatment_label']}")
        lines.append(f"- **Tamanho:** `{row['processed_size_kb']} KB` ({row['bandwidth_saved_pct']}% salvo)")
        lines.append(f"- **WER:** `{row['wer']}` | **Tokens:** `{row['total_tokens']}`")
        if row["error"]:
            lines.append(f"- **Erro:** {row['error']}")
        lines.append(f"> {row['transcript']}")
        lines.append("")
    return "\n".join(lines)
