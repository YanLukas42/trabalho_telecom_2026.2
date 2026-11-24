"""Cliente do Gemini: uma única ponte com a SDK `google-genai`, usada por todos os fluxos."""

import logging
import time
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from telecom import settings

logger = logging.getLogger(__name__)

NON_RETRYABLE_STATUS_CODES = frozenset({400, 401, 403, 404})

_API_ERROR_MESSAGES = {
    400: "A API do Gemini recusou o arquivo enviado (erro 400). Verifique a gravação e tente novamente.",
    401: "Chave da API do Gemini inválida ou sem permissão. Verifique GEMINI_API_KEY no arquivo .env.",
    403: "Chave da API do Gemini inválida ou sem permissão. Verifique GEMINI_API_KEY no arquivo .env.",
    429: "Limite de requisições da API do Gemini atingido. Aguarde alguns instantes e tente novamente.",
}


class GeminiAPIError(ValueError):
    """Falha conhecida ao consultar a API do Gemini, com mensagem segura para o professor."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def describe_api_error(code: int | None, model: str) -> str:
    """Traduz o código de erro da API do Gemini para uma mensagem clara em português."""
    if code is None:
        return "Não foi possível conectar à API do Gemini. Verifique sua conexão com a internet e tente novamente."
    if code == 404:
        return f"O modelo '{model}' não está disponível na API do Gemini. Atualize GEMINI_MODEL no arquivo .env."
    if code in _API_ERROR_MESSAGES:
        return _API_ERROR_MESSAGES[code]
    if 500 <= code < 600:
        return (
            f"A API do Gemini está temporariamente sobrecarregada ou indisponível (erro {code}). "
            "Aguarde alguns instantes e tente novamente."
        )
    return f"A API do Gemini retornou erro {code}. Tente novamente em instantes."


@dataclass(frozen=True)
class GenerationResult:
    text: str
    prompt_tokens: int
    candidate_tokens: int
    total_tokens: int
    latency_sec: float


class GeminiClient:
    """Envia áudio (ou só texto) ao Gemini e devolve o texto com contagem de tokens e latência."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env")
        self._client = genai.Client(api_key=key)
        self.model = model or settings.GEMINI_MODEL

    def generate(
        self,
        audio: bytes,
        mime_type: str,
        prompt: str,
        *,
        response_schema: type | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        max_retries: int = 1,
        backoff_sec: float = 3.5,
    ) -> GenerationResult:
        contents: list[Any] = [types.Part.from_bytes(data=audio, mime_type=mime_type), prompt]
        return self._run(contents, response_schema, temperature, max_output_tokens, max_retries, backoff_sec)

    def generate_text(
        self,
        prompt: str,
        *,
        response_schema: type | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        max_retries: int = 1,
        backoff_sec: float = 3.5,
    ) -> GenerationResult:
        return self._run([prompt], response_schema, temperature, max_output_tokens, max_retries, backoff_sec)

    def _run(
        self,
        contents: list[Any],
        response_schema: type | None,
        temperature: float | None,
        max_output_tokens: int | None,
        max_retries: int,
        backoff_sec: float,
    ) -> GenerationResult:
        """Chama a API. Re-tenta erros transitórios com espera linear (`backoff_sec * tentativa`)."""
        config = _build_config(response_schema, temperature, max_output_tokens)

        for attempt in range(1, max_retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.models.generate_content(model=self.model, contents=contents, config=config)
                break
            except genai_errors.APIError as exc:
                code = getattr(exc, "code", None)
                if code in NON_RETRYABLE_STATUS_CODES or attempt == max_retries:
                    raise GeminiAPIError(describe_api_error(code, self.model), status_code=code) from exc
                last_exc: Exception = exc
            except (ConnectionError, TimeoutError) as exc:
                if attempt == max_retries:
                    raise GeminiAPIError(describe_api_error(None, self.model), status_code=503) from exc
                last_exc = exc
            except Exception as exc:
                if attempt == max_retries:
                    raise
                last_exc = exc
            wait = attempt * backoff_sec
            logger.warning("Erro temporário na API (%s). Nova tentativa em %.1fs.", last_exc, wait)
            time.sleep(wait)

        usage = response.usage_metadata
        prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
        candidate_tokens = getattr(usage, "candidates_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", 0) or (prompt_tokens + candidate_tokens)

        return GenerationResult(
            text=(response.text or "").strip(),
            prompt_tokens=prompt_tokens,
            candidate_tokens=candidate_tokens,
            total_tokens=total_tokens,
            latency_sec=round(time.perf_counter() - started, 3),
        )


def _build_config(
    response_schema: type | None,
    temperature: float | None,
    max_output_tokens: int | None,
) -> types.GenerateContentConfig | None:
    options: dict[str, Any] = {}
    if response_schema is not None:
        options["response_mime_type"] = "application/json"
        options["response_schema"] = response_schema
    if temperature is not None:
        options["temperature"] = temperature
    if max_output_tokens is not None:
        options["max_output_tokens"] = max_output_tokens
    return types.GenerateContentConfig(**options) if options else None
