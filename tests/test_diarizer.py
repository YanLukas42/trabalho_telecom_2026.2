import json

import pytest

from telecom.asr.gemini import GenerationResult
from telecom.diarization import transcriber
from telecom.diarization.transcriber import MAX_OUTPUT_TOKENS, GeminiDiarizer


class StubClient:
    def __init__(self, text):
        self.text = text
        self.kwargs = None

    def generate(self, **kwargs):
        self.kwargs = kwargs
        return GenerationResult(self.text, prompt_tokens=1, candidate_tokens=2, total_tokens=3, latency_sec=0.5)


VALID = json.dumps({"segmentos": [
    {"quemfala": "Juiz", "textodefala": "Olá.", "timestamp": "00:00 - 00:02",
     "segundos_inicio": 0.0, "segundos_fim": 2.0}
]})


def test_sends_whole_file_once_with_full_output_budget(tmp_path):
    audio = tmp_path / "a.opus"
    audio.write_bytes(b"x" * 1000)
    client = StubClient(VALID)

    result = GeminiDiarizer(client).diarize(audio)

    assert client.kwargs["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert client.kwargs["mime_type"] == "audio/ogg"
    assert result.segments[0].speaker == "Juiz"
    assert result.total_tokens == 3


def test_payload_over_inline_limit_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(transcriber, "INLINE_AUDIO_LIMIT_BYTES", 10)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"x" * 100)
    with pytest.raises(ValueError, match="limite inline"):
        GeminiDiarizer(StubClient(VALID)).diarize(audio)


def test_invalid_response_raises_instead_of_writing_empty_report(tmp_path):
    audio = tmp_path / "a.opus"
    audio.write_bytes(b"x")
    with pytest.raises(ValueError, match="JSON válido"):
        GeminiDiarizer(StubClient("não é json")).diarize(audio)
