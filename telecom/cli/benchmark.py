"""CLI de benchmark. Uso: python -m telecom.cli.benchmark {diarizacao,mp3} [--file ARQ] [--dry-run]"""

import argparse
import json
import logging
import sys
from pathlib import Path

from telecom.asr.gemini import GeminiClient
from telecom.benchmark.engine import BenchmarkEngine, GeminiAudioTranscriber
from telecom.benchmark.report import write_benchmark_reports
from telecom.cli.common import configure_logging, media_in_input_dir
from telecom.diarization.prompts import PLAIN_DIARIZATION_PROMPT
from telecom.experiments import MATRICES
from telecom.settings import BENCHMARK_OUTPUT_DIR, DIARIZATION_OUTPUT_DIR

logger = logging.getLogger(__name__)

# Prompt de transcrição simples, usado no benchmark MP3 (fase 1).
PLAIN_TRANSCRIPTION_PROMPT = (
    "Transcreva com máxima precisão o que é falado neste áudio em português. "
    "Retorne APENAS o texto da transcrição, sem introduções, comentários ou formatações extras."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark de tratamentos de áudio com Gemini")
    parser.add_argument("suite", choices=sorted(MATRICES), help="diarizacao (fase 2) ou mp3 (fase 1)")
    parser.add_argument("--file", type=Path, help="Arquivo de entrada. Padrão: todas as mídias de input/")
    parser.add_argument("--dry-run", action="store_true", help="Só prepara os áudios, sem chamar a API")
    parser.add_argument("--model", help="Modelo Gemini (padrão: GEMINI_MODEL ou gemini-2.5-flash)")
    parser.add_argument("--ground-truth", type=Path, help="JSON {nome_do_arquivo: texto_de_referência}")
    args = parser.parse_args(argv)

    configure_logging()
    files = [args.file] if args.file else media_in_input_dir()
    if not files:
        logger.error("Nenhum arquivo de entrada. Use --file ou coloque mídias em input/.")
        return 1

    suite = args.suite
    is_diarization = suite == "diarizacao"
    prompt = PLAIN_DIARIZATION_PROMPT if is_diarization else PLAIN_TRANSCRIPTION_PROMPT
    output_dir = DIARIZATION_OUTPUT_DIR if is_diarization else BENCHMARK_OUTPUT_DIR
    reports_dir = output_dir / "reports"
    audio_dir = output_dir / "audio"
    transcriber = None if args.dry_run else GeminiAudioTranscriber(GeminiClient(model=args.model), prompt)
    ground_truth = json.loads(args.ground_truth.read_text(encoding="utf-8")) if args.ground_truth else {}

    for source in files:
        engine = BenchmarkEngine(
            MATRICES[suite],
            output_dir=audio_dir,
            transcriber=transcriber,
            reference=ground_truth.get(source.name),
            strip_speaker_labels=is_diarization,
        )
        rows = engine.run(source)
        paths = write_benchmark_reports(rows, source, reports_dir)
        logger.info("Relatórios: %s", ", ".join(str(path) for path in paths.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
