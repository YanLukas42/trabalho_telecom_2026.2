from types import SimpleNamespace

from google.genai import errors as genai_errors
import pytest

from telecom.asr.gemini import GeminiAPIError, GeminiClient, describe_api_error
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


def test_generate_text_sends_only_the_prompt():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-x")
    seen = {}
    client._client.models.generate_content = lambda **kwargs: seen.update(kwargs) or _response(text="ok")
    result = client.generate_text("só texto")
    assert seen["contents"] == ["só texto"]
    assert result.text == "ok"


@pytest.mark.parametrize(
    ("code", "expected_fragment"),
    [
        (401, "Chave da API do Gemini inválida"),
        (403, "Chave da API do Gemini inválida"),
        (404, "modelo 'gemini-3.8-flash' não está disponível"),
        (429, "Limite de requisições"),
        (503, "sobrecarregada ou indisponível (erro 503)"),
        (400, "recusou o arquivo enviado (erro 400)"),
        (None, "Não foi possível conectar"),
    ],
)
def test_describe_api_error_translates_known_codes(code, expected_fragment):
    message = describe_api_error(code, "gemini-3.8-flash")
    assert expected_fragment in message


def test_api_404_fails_without_retrying():
    client = GeminiClient(api_key="chave-de-teste", model="modelo-indisponivel")
    attempts = {"count": 0}

    def fail_404(**kwargs):
        attempts["count"] += 1
        raise genai_errors.ClientError(404, {"error": {"code": 404, "message": "not found"}}, None)

    client._client.models.generate_content = fail_404
    with pytest.raises(GeminiAPIError, match="modelo-indisponivel") as exc_info:
        client.generate(b"a", "audio/mp3", "p", max_retries=4, backoff_sec=0.0)
    assert attempts["count"] == 1
    assert exc_info.value.status_code == 404


def test_api_503_retries_then_raises_friendly_error():
    client = GeminiClient(api_key="chave-de-teste", model="gemini-3.8-flash")
    attempts = {"count": 0}

    def fail_503(**kwargs):
        attempts["count"] += 1
        raise genai_errors.ServerError(503, {"error": {"code": 503, "message": "high demand"}}, None)

    client._client.models.generate_content = fail_503
    with pytest.raises(GeminiAPIError, match="sobrecarregada ou indisponível \\(erro 503\\)") as exc_info:
        client.generate(b"a", "audio/mp3", "p", max_retries=3, backoff_sec=0.0)
    assert attempts["count"] == 3
    assert exc_info.value.status_code == 503


def test_connection_error_retries_then_raises_friendly_error():
    client = GeminiClient(api_key="chave-de-teste", model="gemini-3.8-flash")
    attempts = {"count": 0}

    def fail_network(**kwargs):
        attempts["count"] += 1
        raise ConnectionError("network unreachable")

    client._client.models.generate_content = fail_network
    with pytest.raises(GeminiAPIError, match="Não foi possível conectar") as exc_info:
        client.generate(b"a", "audio/mp3", "p", max_retries=2, backoff_sec=0.0)
    assert attempts["count"] == 2
    assert exc_info.value.status_code == 503
