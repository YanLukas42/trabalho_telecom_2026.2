"""Construção dos diarizadores e verificação de disponibilidade. Compartilhado pela CLI e pela interface web."""

import importlib.util

from telecom.asr.gemini import GeminiClient
from telecom.diarization.models import Diarizer
from telecom.settings import GEMINI_API_KEY, HF_TOKEN

ENGINES = ("gemini", "pyannote")
DEFAULT_CODEC = {"pyannote": "wav", "gemini": "opus"}
LOCAL_ENGINE_MODULES = ("pyannote.audio", "faster_whisper")


def engine_unavailable_reason(engine: str) -> str | None:
    """Motivo pelo qual o motor não pode rodar nesta máquina, ou None se estiver pronto."""
    if engine == "gemini":
        return None if GEMINI_API_KEY else "GEMINI_API_KEY não configurada no .env."
    if engine == "pyannote":
        if not HF_TOKEN:
            return "HF_TOKEN não configurado no .env."
        missing = [name for name in LOCAL_ENGINE_MODULES if not _installed(name)]
        if missing:
            return f"Dependências locais ausentes ({', '.join(missing)}). Instale requirements-local.txt."
        return None
    raise ValueError(f"Motor desconhecido: {engine}")


def build_diarizer(
    engine: str,
    *,
    model: str | None = None,
    whisper_model: str = "small",
    device: str = "cpu",
    language: str = "pt",
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    prompt: str | None = None,
) -> Diarizer:
    if engine == "gemini":
        from telecom.diarization.transcriber import GeminiDiarizer

        return GeminiDiarizer(GeminiClient(model=model), prompt=prompt)

    if engine != "pyannote":
        raise ValueError(f"Motor desconhecido: {engine}")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN não configurado no .env. O modelo do pyannote é restrito no Hugging Face.")

    from telecom.diarization.pyannote_whisper import build_local_diarizer

    return build_local_diarizer(
        hf_token=HF_TOKEN,
        whisper_model=whisper_model,
        device=device,
        language=language,
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )


def _installed(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False
