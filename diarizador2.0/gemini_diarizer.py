"""
Cliente Gemini Especializado em Diarização de Falantes.
Transcreve e rotula a fala separando cada interlocutor com identificação e timestamps aproximados.
"""

import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

DIARIZADOR_DIR = Path(__file__).resolve().parent
if str(DIARIZADOR_DIR) not in sys.path:
    sys.path.insert(0, str(DIARIZADOR_DIR))

from config_diarizador import GEMINI_API_KEY, DEFAULT_MODEL


class GeminiDiarizer:
    """Interface para Diarização e Transcrição com Google Gemini Multimodal."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            self.client = None
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except Exception:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self.client = legacy_genai
            self.sdk_type = "google-generativeai"

    def diarize(self, audio_path: Path) -> Dict[str, Any]:
        """
        Envia áudio para a API do Gemini com instrução especializada de Diarização.
        Retorna transcrição estruturada com falantes e metadados de tokens/latência.
        """
        audio_path = Path(audio_path)
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env!")

        prompt = (
            "Você é um especialista em transcrição jurídica e telecomunicações. "
            "Transcreva com máxima precisão o áudio em português realizando a DIARIZAÇÃO COMPLETA DOS FALANTES.\n"
            "Regras:\n"
            "1. Identifique e separe cada pessoa que fala (ex: [Juiz], [Réu / Bruno], [Defensora], [Promotor] ou [Falante 1], [Falante 2]).\n"
            "2. Mantenha os turnos de fala separados por parágrafos.\n"
            "3. Não invente palavras e capture nomes, números e endereços com fidelidade.\n"
            "4. Retorne apenas a transcrição diarizada, sem comentários adicionais."
        )

        start_time = time.time()
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        if self.sdk_type == "google-genai":
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"),
                    prompt
                ]
            )
            latency_sec = round(time.time() - start_time, 3)
            transcript = response.text.strip() if response.text else ""
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or (prompt_tokens + candidate_tokens)
        else:
            model = self.client.GenerativeModel(self.model_name)
            response = model.generate_content([
                {"mime_type": "audio/mp3", "data": audio_bytes},
                prompt
            ])
            latency_sec = round(time.time() - start_time, 3)
            transcript = response.text.strip() if hasattr(response, "text") and response.text else ""
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

        return {
            "diarized_transcript": transcript,
            "prompt_tokens": prompt_tokens,
            "candidate_tokens": candidate_tokens,
            "total_tokens": total_tokens,
            "api_latency_sec": latency_sec
        }
