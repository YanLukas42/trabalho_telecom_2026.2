"""
Configurações para o Diarizador 2.0.
Focado em Diarização de Falantes, Áudio Contínuo (Sem VAD) e Sem Normalização Pesada.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DIARIZADOR_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = DIARIZADOR_DIR / "output"
PROCESSED_AUDIO_DIR = OUTPUT_DIR / "audio"
REPORTS_DIR = OUTPUT_DIR / "reports"

for d in [PROCESSED_AUDIO_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Matriz de Testes Otimizada para Diarização
# 1. Sem VAD (preserva tempo e pausas)
# 2. Sem loudnorm (processamento local <1s)
# 3. Filtro Wideband de voz (80Hz - 7.5kHz) que protege formantes de falantes
DIARIZATION_EXPERIMENT_MATRIX = [
    {
        "id": "01_baseline_320k_stereo",
        "label": "Baseline 320k Estéreo (Máxima Fidelidade)",
        "bitrate": "320k",
        "sample_rate": 44100,
        "channels": 2,
        "filter_wideband": False,
        "is_baseline": True
    },
    {
        "id": "02_bitrate_128k_stereo",
        "label": "MP3 128k Estéreo (Padrão)",
        "bitrate": "128k",
        "sample_rate": 44100,
        "channels": 2,
        "filter_wideband": False,
        "is_baseline": False
    },
    {
        "id": "03_bitrate_64k_mono_wideband",
        "label": "MP3 64k Mono + Filtro Voz Wideband",
        "bitrate": "64k",
        "sample_rate": 16000,
        "channels": 1,
        "filter_wideband": True,
        "is_baseline": False
    },
    {
        "id": "04_bitrate_32k_mono_wideband",
        "label": "MP3 32k Mono + Filtro Voz Wideband",
        "bitrate": "32k",
        "sample_rate": 16000,
        "channels": 1,
        "filter_wideband": True,
        "is_baseline": False
    },
    {
        "id": "05_bitrate_16k_mono_wideband",
        "label": "MP3 16k Mono + Filtro Voz Wideband",
        "bitrate": "16k",
        "sample_rate": 16000,
        "channels": 1,
        "filter_wideband": True,
        "is_baseline": False
    },
    {
        "id": "06_bitrate_8k_mono_wideband",
        "label": "MP3 8k Mono + Filtro Voz Wideband (Ultra-leve)",
        "bitrate": "8k",
        "sample_rate": 16000,
        "channels": 1,
        "filter_wideband": True,
        "is_baseline": False
    },
    {
        "id": "07_bitrate_32k_stereo_spatial",
        "label": "MP3 32k Estéreo (Espacialidade para Diarização)",
        "bitrate": "32k",
        "sample_rate": 24000,
        "channels": 2,
        "filter_wideband": False,
        "is_baseline": False
    }
]
