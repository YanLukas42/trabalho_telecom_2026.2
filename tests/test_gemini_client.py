from types import SimpleNamespace

import pytest

from telecom.asr.gemini import GeminiClient
from telecom.asr.schemas import TranscricaoChunkDiarizada


def _response(text="ok", prompt=10, candidates=5):
    usage = SimpleNamespace(prompt_token_count=prompt, candidates_token_count=candidates, total_token_count=None)
    return SimpleNamespace(text=text, usage_metadata=usage)


def test_missing_key_is_rejected(monkeypatch):
    monkeypatch.setattr("telecom.settings.GEMINI_API_KEY", "")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiClient(api_key="")


def test_generate_sends_schema_config_and_reads_usage():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-x")
    calls = []

    def fake_generate(model, contents, config):
        calls.append({"model": model, "contents": contents, "config": config})
        return _response(text="  texto  ")

    client._client.models.generate_content = fake_generate
    result = client.generate(
        b"audio", "audio/ogg", "prompt",
        response_schema=TranscricaoChunkDiarizada, temperature=0.1, max_output_tokens=8192,
    )

    call = calls[0]
    assert call["model"] == "modelo-x"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is TranscricaoChunkDiarizada
    assert call["config"].temperature == 0.1
    assert call["config"].max_output_tokens == 8192
    assert result.text == "texto"
    assert (result.prompt_tokens, result.candidate_tokens, result.total_tokens) == (10, 5, 15)


def test_generate_without_options_sends_no_config():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-x")
    seen = {}
    client._client.models.generate_content = lambda **kwargs: seen.update(kwargs) or _response()
    client.generate(b"audio", "audio/mp3", "prompt")
    assert seen["config"] is None


def test_transient_error_is_retried_then_succeeds():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-x")
    attempts = {"count": 0}

    def flaky(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("429 rate limit")
        return _response()

    client._client.models.generate_content = flaky
    result = client.generate(b"a", "audio/mp3", "p", max_retries=3, backoff_sec=0.0)
    assert attempts["count"] == 2
    assert result.text == "ok"


def test_error_after_last_retry_is_raised():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-x")

    def always_fails(**kwargs):
        raise RuntimeError("indisponível")

    client._client.models.generate_content = always_fails
    with pytest.raises(RuntimeError, match="indisponível"):
        client.generate(b"a", "audio/mp3", "p", max_retries=2, backoff_sec=0.0)
