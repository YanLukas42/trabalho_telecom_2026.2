"""
Benchmark Runner Engine.
Orchestrates audio treatments, API transcribing, metric computation, and aggregation.
"""

import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import (
    PROCESSED_AUDIO_DIR,
    GROUND_TRUTH_FILE,
    EXPERIMENT_MATRIX,
    DEFAULT_GEMINI_MODEL
)
from src.audio_processing.mp3_encoder import MP3Encoder
from src.audio_processing.filters import AudioFilters
from src.audio_processing.vad import VoiceActivityDetector
from src.audio_processing.normalizer import AudioNormalizer
from src.evaluators.accuracy import AccuracyEvaluator
from src.evaluators.cost_latency import CostLatencyEvaluator
from src.gemini.client import GeminiAudioTranscriber


class BenchmarkRunner:
    """Runs audio benchmark experiments against the configured matrix."""

    def __init__(self, gemini_api_key: Optional[str] = None, model_name: str = DEFAULT_GEMINI_MODEL):
        self.encoder = MP3Encoder()
        self.transcriber = GeminiAudioTranscriber(api_key=gemini_api_key, model_name=model_name)
        self.ground_truth = self._load_ground_truth()

    def _load_ground_truth(self) -> Dict[str, str]:
        """Loads ground truth transcriptions dictionary."""
        if GROUND_TRUTH_FILE.exists():
            try:
                with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def process_treatment(
        self,
        input_audio: Path,
        treatment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applies audio transformation parameters (bitrate, sample rate, filters, vad, normalizer)
        and outputs a test MP3.
        """
        sample_name = input_audio.stem
        output_filename = f"{sample_name}_{treatment['id']}.mp3"
        output_path = PROCESSED_AUDIO_DIR / output_filename

        # Build FFmpeg filter chain
        filters_list = []

        if treatment.get("filter"):
            f_str = AudioFilters.get_filter_string(treatment["filter"])
            if f_str:
                filters_list.append(f_str)

        if treatment.get("vad"):
            v_str = VoiceActivityDetector.get_vad_filter_string()
            filters_list.append(v_str)

        if treatment.get("normalize"):
            n_str = AudioNormalizer.get_loudnorm_filter_string()
            filters_list.append(n_str)

        extra_filters = ",".join(filters_list) if filters_list else None

        t0 = time.time()
        meta = self.encoder.transcode(
            input_path=input_audio,
            output_path=output_path,
            bitrate=treatment.get("bitrate", "128k"),
            sample_rate=treatment.get("sample_rate", 44100),
            channels=treatment.get("channels", 2),
            extra_audio_filters=extra_filters
        )
        preprocess_latency = round(time.time() - t0, 3)
        meta["preprocess_latency_sec"] = preprocess_latency
        return meta

    def run_experiment_on_file(
        self,
        audio_file: Path,
        dry_run: bool = False,
        treatment_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Runs the benchmark suite on a single audio file."""
        audio_file = Path(audio_file)
        sample_key = audio_file.name
        ref_text = self.ground_truth.get(sample_key, "")

        original_size = audio_file.stat().st_size
        results = []

        active_treatments = EXPERIMENT_MATRIX
        if treatment_ids:
            active_treatments = [t for t in EXPERIMENT_MATRIX if t["id"] in treatment_ids]

        print(f"\n=======================================================")
        print(f"▶ Analisando Arquivo: {audio_file.name}")
        print(f"  Tamanho Original: {round(original_size / 1024, 2)} KB")
        print(f"  Ground Truth: '{ref_text[:60]}...' " if ref_text else "  [Aviso: Sem Ground Truth cadastrado]")
        print(f"=======================================================")

        for t in active_treatments:
            t_id = t["id"]
            t_label = t["label"]
            category = t["category"]
            print(f"  ⚡ [{category}] Processando: {t_label}...", end=" ", flush=True)

            # 1. Process audio to MP3
            meta = self.process_treatment(audio_file, t)
            proc_path = Path(meta["output_path"])
            proc_size = meta["file_size_bytes"]

            # Compression stats
            comp = CostLatencyEvaluator.calculate_compression_stats(original_size, proc_size)

            # 2. Transcribe (if not dry-run)
            transcript = ""
            prompt_tokens = 0
            candidate_tokens = 0
            total_tokens = 0
            api_latency = 0.0
            wer = 0.0
            cer = 0.0

            if not dry_run:
                try:
                    res = self.transcriber.transcribe(proc_path)
                    transcript = res["transcript"]
                    prompt_tokens = res["prompt_tokens"]
                    candidate_tokens = res["candidate_tokens"]
                    total_tokens = res["total_tokens"]
                    api_latency = res["latency_sec"]

                    if ref_text:
                        acc = AccuracyEvaluator.evaluate(ref_text, transcript)
                        wer = acc["wer"]
                        cer = acc["cer"]

                    print(f"OK | WER: {wer}% | Tokens: {total_tokens} | API: {api_latency}s")
                except Exception as e:
                    print(f"FALHA API: {e}")
                    transcript = f"[ERRO: {e}]"
            else:
                print(f"OK (Dry-Run: {meta['file_size_kb']} KB)")

            # Cost estimate
            cost = CostLatencyEvaluator.estimate_cost(prompt_tokens, candidate_tokens)

            row = {
                "sample_file": audio_file.name,
                "treatment_id": t_id,
                "treatment_label": t_label,
                "category": category,
                "bitrate": meta["bitrate"],
                "sample_rate": meta["sample_rate"],
                "channels": meta["channels"],
                "duration_sec": meta["duration_sec"],
                "original_size_kb": round(original_size / 1024, 2),
                "processed_size_kb": meta["file_size_kb"],
                "compression_ratio": comp["compression_ratio"],
                "bandwidth_saved_pct": comp["bandwidth_saved_pct"],
                "preprocess_latency_sec": meta["preprocess_latency_sec"],
                "api_latency_sec": api_latency,
                "total_latency_sec": round(meta["preprocess_latency_sec"] + api_latency, 3),
                "prompt_tokens": prompt_tokens,
                "candidate_tokens": candidate_tokens,
                "total_tokens": total_tokens,
                "wer": wer,
                "cer": cer,
                "estimated_cost_usd": cost["total_cost_usd"],
                "estimated_cost_brl": cost["total_cost_brl"],
                "transcript": transcript,
                "ground_truth": ref_text
            }
            results.append(row)

        return results
