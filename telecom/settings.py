"""Configuração central: caminhos, variáveis de ambiente e tarifas. Sem efeitos colaterais na importação."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
DIARIZATION_OUTPUT_DIR = OUTPUT_DIR / "diarizacao"
BENCHMARK_OUTPUT_DIR = OUTPUT_DIR / "benchmark"

# Arquivos preferidos quando o diarizador roda sem --file.
DEFAULT_DIARIZATION_INPUTS = ("videoplayback.mp4", "999.mp4")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Tarifas do Gemini Flash (USD por 1M de tokens) e câmbio de referência.
PRICE_INPUT_USD_PER_M = 0.15
PRICE_OUTPUT_USD_PER_M = 0.60
USD_TO_BRL = 5.70

MEDIA_EXTENSIONS = (".mp4", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mkv", ".webm")
