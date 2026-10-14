from telecom.asr.repair import parse_chunk_json


def test_valid_json_is_returned_as_is():
    data = parse_chunk_json('{"segmentos": []}')
    assert data == {"segmentos": []}


def test_truncated_response_keeps_complete_segments():
    raw = (
        '{"segmentos": [{"quemfala": "Juiz", "textodefala": "Olá.", "timestamp": "00:00 - 00:02", '
        '"segundos_inicio": 0.0, "segundos_fim": 2.0}, '
        '{"quemfala": "Réu", "textodefala": "Oi"'
    )
    data = parse_chunk_json(raw)
    assert data is not None
    assert [seg["quemfala"] for seg in data["segmentos"]] == ["Juiz"]


def test_garbage_returns_none():
    assert parse_chunk_json("não é json") is None
