"""Escrita de relatórios em CSV, JSON e Markdown, sem dependências pesadas."""

import csv
import json
from pathlib import Path
from typing import Any, Sequence


def write_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(rows: Sequence[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # União das chaves de todas as linhas: linhas com erro podem ter menos campos.
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, restval="")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: Sequence[dict[str, Any]], columns: Sequence[str]) -> str:
    """Tabela Markdown com as colunas dadas, na ordem dada."""
    header = "| " + " | ".join(columns) + " |"
    divider = "|" + "|".join(":---" for _ in columns) + "|"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in columns) + " |" for row in rows]
    return "\n".join([header, divider, *body])
