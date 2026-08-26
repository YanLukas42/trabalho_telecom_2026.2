"""
Report Generator for Benchmark Results.
Outputs Markdown tables, CSV datasets, and JSON records.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from tabulate import tabulate

from config import REPORTS_DIR


class ReportGenerator:
    """Generates structured benchmark reports."""

    @staticmethod
    def export_all(results: List[Dict[str, Any]], filename_prefix: str = "benchmark_results") -> Dict[str, Path]:
        """Saves results in CSV, JSON, and Markdown formats."""
        if not results:
            return {}

        df = pd.DataFrame(results)

        csv_path = REPORTS_DIR / f"{filename_prefix}.csv"
        json_path = REPORTS_DIR / f"{filename_prefix}.json"
        md_path = REPORTS_DIR / f"{filename_prefix}.md"

        # Export CSV
        df.to_csv(csv_path, index=False, encoding="utf-8")

        # Export JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Export Markdown Table
        summary_cols = [
            "treatment_label",
            "processed_size_kb",
            "bandwidth_saved_pct",
            "wer",
            "cer",
            "total_tokens",
            "total_latency_sec",
            "estimated_cost_usd"
        ]
        
        # Filter available columns
        available_cols = [c for c in summary_cols if c in df.columns]
        summary_df = df[available_cols]

        md_content = f"# Relatório de Benchmark: Tratamentos de MP3 vs. Gemini API\n\n"
        md_content += f"Total de Experimentos Executados: **{len(results)}**\n\n"
        md_content += summary_df.to_markdown(index=False)
        md_content += "\n\n## Detalhes das Transcrições Obtidas\n\n"

        for idx, row in df.iterrows():
            md_content += f"### {row.get('treatment_label', 'Experimento')}\n"
            md_content += f"- **Arquivo:** `{row.get('sample_file')}` | **Tamanho:** `{row.get('processed_size_kb')} KB` ({row.get('bandwidth_saved_pct')}% salvo)\n"
            md_content += f"- **WER:** `{row.get('wer')}%` | **Tokens:** `{row.get('total_tokens')}` | **Latência:** `{row.get('total_latency_sec')}s`\n"
            md_content += f"- **Transcrição:**\n> {row.get('transcript', '')}\n\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {
            "csv": csv_path,
            "json": json_path,
            "md": md_path
        }
