"""
Google Gemini Multimodal Audio Client.
Handles uploading/sending MP3 audio payloads, measuring exact round-trip latency,
and extracting usage_metadata (prompt tokens, response tokens).
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL


class GeminiAudioTranscriber:
    """Interface to transcribe audio using Google Gemini Multimodal API."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_GEMINI_MODEL):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._init_client()

    def _init_client(self):
        """Initializes Google GenAI client."""
        if not self.api_key:
            # Client can be instantiated without key for dry-run or will warn on call
            self.client = None
            return

        # Attempt to use google.genai (new SDK) or fallback to google.generativeai
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except Exception:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai
                self.sdk_type = "google-generativeai"
            except Exception as e:
                self.client = None
                self.sdk_type = None

    def transcribe(self, audio_path: Path, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends MP3 audio file to Gemini for speech transcription.
        Returns:
            - transcription text
            - prompt_tokens
            - candidate_tokens
            - total_tokens
            - latency_sec (API response time)
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        prompt = custom_prompt or (
            "Transcreva com máxima precisão o que é falado neste áudio em português. "
            "Retorne APENAS o texto da transcrição, sem introduções, comentários ou formatações extras."
        )

        start_time = time.time()

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada! Por favor, adicione sua chave no arquivo .env"
            )

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
            prompt_tokens = 0
            candidate_tokens = 0
            total_tokens = 0

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or (prompt_tokens + candidate_tokens)

        else:
            # Legacy SDK fallback
            model = self.client.GenerativeModel(self.model_name)
            response = model.generate_content([
                {"mime_type": "audio/mp3", "data": audio_bytes},
                prompt
            ])
            latency_sec = round(time.time() - start_time, 3)
            transcript = response.text.strip() if hasattr(response, "text") and response.text else ""
            
            prompt_tokens = 0
            candidate_tokens = 0
            total_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

        return {
            "transcript": transcript,
            "prompt_tokens": prompt_tokens,
            "candidate_tokens": candidate_tokens,
            "total_tokens": total_tokens,
            "latency_sec": latency_sec
        }
