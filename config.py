"""
Central Configuration for MP3-Gemini Optimizer Benchmark.
Defines paths, experiment parameters, audio treatment matrices, and pricing models.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
DATASET_DIR = BASE_DIR / "dataset"
SAMPLES_DIR = DATASET_DIR / "samples"
GROUND_TRUTH_FILE = DATASET_DIR / "ground_truth.json"

OUTPUT_DIR = BASE_DIR / "output"
PROCESSED_AUDIO_DIR = OUTPUT_DIR / "mp3_variations"
PLOTS_DIR = OUTPUT_DIR / "plots"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Ensure runtime directories exist
for folder in [INPUT_DIR, SAMPLES_DIR, PROCESSED_AUDIO_DIR, PLOTS_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Google Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Approximate Gemini Multimodal Pricing (USD per 1M tokens) - Updated for Flash tiers
PRICING_PER_1M_INPUT_TOKENS = 0.15   # USD ($0.15 / 1M tokens for Flash)
PRICING_PER_1M_OUTPUT_TOKENS = 0.60  # USD ($0.60 / 1M tokens for Flash)
USD_TO_BRL = 5.70                    # Currency conversion factor

# Audio Treatment Experiment Matrix
EXPERIMENT_MATRIX = [
    {
        "id": "01_baseline_320k_stereo",
        "label": "Baseline 320k (Stereo 44.1kHz)",
        "bitrate": "320k",
        "sample_rate": 44100,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "02_bitrate_192k",
        "label": "MP3 192k (Stereo 44.1kHz)",
        "bitrate": "192k",
        "sample_rate": 44100,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "03_bitrate_128k",
        "label": "MP3 128k (Stereo 44.1kHz)",
        "bitrate": "128k",
        "sample_rate": 44100,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "04_bitrate_64k",
        "label": "MP3 64k (Stereo 44.1kHz)",
        "bitrate": "64k",
        "sample_rate": 44100,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "05_bitrate_32k",
        "label": "MP3 32k (Stereo 44.1kHz)",
        "bitrate": "32k",
        "sample_rate": 44100,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "06_bitrate_16k",
        "label": "MP3 16k (Mono 22.05kHz)",
        "bitrate": "16k",
        "sample_rate": 22050,
        "channels": 1,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "07_bitrate_8k",
        "label": "MP3 8k (Mono 16kHz - Ultra-compressed)",
        "bitrate": "8k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Bitrate Sweep"
    },
    {
        "id": "08_sample_rate_24k",
        "label": "Sample Rate 24kHz (128k Stereo)",
        "bitrate": "128k",
        "sample_rate": 24000,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Sample Rate Sweep"
    },
    {
        "id": "09_sample_rate_16k",
        "label": "Sample Rate 16kHz (128k Stereo)",
        "bitrate": "128k",
        "sample_rate": 16000,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Sample Rate Sweep"
    },
    {
        "id": "10_sample_rate_8k",
        "label": "Sample Rate 8kHz Telephony (64k Stereo)",
        "bitrate": "64k",
        "sample_rate": 8000,
        "channels": 2,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Sample Rate Sweep"
    },
    {
        "id": "11_mono_downmix",
        "label": "Downmix to Mono (128k 44.1kHz)",
        "bitrate": "128k",
        "sample_rate": 44100,
        "channels": 1,
        "filter": None,
        "vad": False,
        "normalize": False,
        "category": "Channel Optimization"
    },
    {
        "id": "12_filter_telecom_narrowband",
        "label": "Filtro Telefonia Narrowband (300Hz-3.4kHz)",
        "bitrate": "64k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": {"type": "bandpass", "low": 300, "high": 3400},
        "vad": False,
        "normalize": False,
        "category": "Acoustic Filtering"
    },
    {
        "id": "13_filter_voice_wideband",
        "label": "Filtro Voz Humana Wideband (80Hz-7.5kHz)",
        "bitrate": "64k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": {"type": "bandpass", "low": 80, "high": 7500},
        "vad": False,
        "normalize": False,
        "category": "Acoustic Filtering"
    },
    {
        "id": "14_vad_silence_stripping",
        "label": "VAD (Corte de Silêncio e Pausas)",
        "bitrate": "64k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": None,
        "vad": True,
        "normalize": False,
        "category": "Temporal / VAD"
    },
    {
        "id": "15_loudness_normalized",
        "label": "Normalização de Ganho / Volume",
        "bitrate": "64k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": None,
        "vad": False,
        "normalize": True,
        "category": "Dynamic Range"
    },
    {
        "id": "16_ai_optimized_mp3_candidate",
        "label": "⭐ MP3 Otimizado para IA (Novo MP3)",
        "bitrate": "32k",
        "sample_rate": 16000,
        "channels": 1,
        "filter": {"type": "bandpass", "low": 80, "high": 7500},
        "vad": True,
        "normalize": True,
        "category": "AI Optimized Recipe"
    }
]
