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
# Cada transcrição feita pela interface web ganha uma pasta própria aqui.
WEB_JOBS_DIR = DIARIZATION_OUTPUT_DIR / "jobs"
TENANTS_DIR = OUTPUT_DIR / "tenants"
def resolve_db_path(raw_env: str | None = None) -> Path:
    """Resolve o caminho do SQLite a partir de PAUTA_DB_PATH, com padrão output/pauta.db."""
    candidate = (os.getenv("PAUTA_DB_PATH", "") if raw_env is None else raw_env).strip()
    return Path(candidate) if candidate else OUTPUT_DIR / "pauta.db"


DATABASE_PATH = resolve_db_path()

# Arquivos preferidos quando o diarizador roda sem --file.
DEFAULT_DIARIZATION_INPUTS = ("videoplayback.mp4", "999.mp4")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Token de leitura do Hugging Face: necessário para os modelos restritos do pyannote.
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Tarifas do Gemini Flash (USD por 1M de tokens) e câmbio de referência.
PRICE_INPUT_USD_PER_M = 0.15
PRICE_OUTPUT_USD_PER_M = 0.60
USD_TO_BRL = 5.70

# Autenticação e cookies de sessão
PAUTA_COOKIE_SECURE = os.getenv("PAUTA_COOKIE_SECURE", "0") == "1"
SESSION_COOKIE_NAME = "pauta_session"
SESSION_DURATION_HOURS = 12

MEDIA_EXTENSIONS = (".mp4", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mkv", ".webm")
