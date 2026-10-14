"""Cliente do Gemini: uma única ponte com a SDK `google-genai`, usada por todos os fluxos."""

import logging
import time
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from telecom import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerationResult:
    text: str
    prompt_tokens: int
    candidate_tokens: int
    total_tokens: int
    latency_sec: float


class GeminiClient:
    """Envia áudio + prompt ao Gemini e devolve o texto com contagem de tokens e latência."""

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
        """Chama a API. Re-tenta erros transitórios com espera linear (`backoff_sec * tentativa`)."""
        config = _build_config(response_schema, temperature, max_output_tokens)
        contents: list[Any] = [types.Part.from_bytes(data=audio, mime_type=mime_type), prompt]

        for attempt in range(1, max_retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.models.generate_content(model=self.model, contents=contents, config=config)
                break
            except Exception as exc:
                if attempt == max_retries:
                    raise
                wait = attempt * backoff_sec
                logger.warning("Erro temporário na API (%s). Nova tentativa em %.1fs.", exc, wait)
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
