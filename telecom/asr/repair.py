"""Recuperação de JSON truncado ou malformado devolvido pelo modelo."""

import json
import re
from typing import Any

# Um segmento completo: objeto sem chaves aninhadas com os campos de fala.
_SEGMENT_PATTERN = re.compile(r'\{[^{}]*"quemfala"[^{}]*"textodefala"[^{}]*\}', re.DOTALL)


def parse_chunk_json(raw_text: str) -> dict[str, Any] | None:
    """Tenta obter um dicionário `{"segmentos": [...]}` mesmo quando a resposta está cortada.

    Ordem das tentativas: JSON íntegro; segmentos completos reagrupados; fechamento do array após a última chave.
    """
    attempts = [
        lambda: json.loads(raw_text),
        lambda: _rebuild_from_complete_segments(raw_text),
        lambda: json.loads(raw_text[: raw_text.rfind("}") + 1] + "]}"),
    ]
    for attempt in attempts:
        try:
            data = attempt()
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return None


def _rebuild_from_complete_segments(raw_text: str) -> dict[str, Any]:
    matches = _SEGMENT_PATTERN.findall(raw_text)
    if not matches:
        raise ValueError("nenhum segmento completo encontrado")
    return json.loads('{"segmentos": [' + ",".join(matches) + "]}")
