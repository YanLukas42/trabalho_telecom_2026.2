"""
Testes unitários para o módulo VAD e correção de timestamps do Diarizador 2.0.
"""

import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIARIZADOR_DIR = PROJECT_ROOT / "diarizador2.0"

for p in [str(PROJECT_ROOT), str(DIARIZADOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from vad_compact import map_compact_to_original, VadAudioCompactor, format_seconds_to_timestamp


def test_map_compact_to_original_exact_blocks():
    """Testa a lógica de mapeamento nos blocos de exemplo."""
    segments_map = [
        {"orig_start": 10.0, "orig_end": 25.0, "comp_start": 0.0, "comp_end": 15.0},
        {"orig_start": 40.0, "orig_end": 70.0, "comp_start": 15.0, "comp_end": 45.0},
        {"orig_start": 90.0, "orig_end": 110.0, "comp_start": 45.0, "comp_end": 65.0},
    ]

    # Início do Bloco 1 (0.0s compacto -> 10.0s original)
    assert map_compact_to_original(0.0, segments_map) == 10.0

    # Meio do Bloco 1 (5.0s compacto -> 15.0s original)
    assert map_compact_to_original(5.0, segments_map) == 15.0

    # Fim do Bloco 1 (15.0s compacto -> 25.0s original)
    assert map_compact_to_original(15.0, segments_map) == 25.0

    # Início do Bloco 2 (15.0s compacto -> 25.0s ou 40.0s na fronteira)
    # 20.0s compacto está no Bloco 2: 40.0 + (20.0 - 15.0) = 45.0s original
    assert map_compact_to_original(20.0, segments_map) == 45.0

    # Meio do Bloco 3 (50.0s compacto -> 90.0 + (50.0 - 45.0) = 95.0s original)
    assert map_compact_to_original(50.0, segments_map) == 95.0


def test_map_compact_to_original_edge_cases():
    """Testa limites, arredondamentos extremos e mapas vazios."""
    segments_map = [
        {"orig_start": 10.0, "orig_end": 25.0, "comp_start": 0.0, "comp_end": 15.0},
        {"orig_start": 40.0, "orig_end": 70.0, "comp_start": 15.0, "comp_end": 45.0},
    ]

    # Timestamp além do último frame por arredondamento
    assert map_compact_to_original(50.0, segments_map) == 70.0

    # Timestamp antes do primeiro bloco (negativo ou arredondamento)
    assert map_compact_to_original(-1.0, segments_map) == 10.0

    # Mapa vazio: deve retornar o próprio valor
    assert map_compact_to_original(12.5, []) == 12.5


def test_format_seconds_to_timestamp():
    """Testa conversão de segundos para MM:SS e HH:MM:SS."""
    assert format_seconds_to_timestamp(0.0) == "00:00"
    assert format_seconds_to_timestamp(45.2) == "00:45"
    assert format_seconds_to_timestamp(125.0) == "02:05"
    assert format_seconds_to_timestamp(3665.0) == "01:01:05"


def test_remap_diarized_segments():
    """Testa remapeamento de lista de segmentos de diarização."""
    segments_map = [
        {"orig_start": 10.0, "orig_end": 25.0, "comp_start": 0.0, "comp_end": 15.0},
        {"orig_start": 40.0, "orig_end": 70.0, "comp_start": 15.0, "comp_end": 45.0},
    ]

    raw_segments = [
        {
            "quemfala": "Juiz",
            "textodefala": "Iniciando a audiência.",
            "segundos_inicio": 2.0,
            "segundos_fim": 8.0,
            "timestamp": "00:02 - 00:08"
        },
        {
            "quemfala": "Réu",
            "textodefala": "Presente, excelência.",
            "segundos_inicio": 20.0,
            "segundos_fim": 25.0,
            "timestamp": "00:20 - 00:25"
        }
    ]

    remapped = VadAudioCompactor.remap_diarized_segments(raw_segments, segments_map)

    # Segmento 1: 2.0s -> 12.0s | 8.0s -> 18.0s
    assert remapped[0]["segundos_inicio"] == 12.0
    assert remapped[0]["segundos_fim"] == 18.0
    assert remapped[0]["timestamp"] == "00:12 - 00:18"
    assert remapped[0]["segundos_inicio_compact"] == 2.0

    # Segmento 2: 20.0s -> 45.0s | 25.0s -> 50.0s
    assert remapped[1]["segundos_inicio"] == 45.0
    assert remapped[1]["segundos_fim"] == 50.0
    assert remapped[1]["timestamp"] == "00:45 - 00:50"
    assert remapped[1]["segundos_inicio_compact"] == 20.0
