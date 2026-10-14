"""CLI de diarização. Uso: python -m telecom.cli.diarize [--file ARQ] [--codec opus|mp3] [--vad]"""

import argparse
import logging
import sys
from pathlib import Path

from telecom.asr.gemini import GeminiClient
from telecom.cli.common import configure_logging, media_in_input_dir
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.diarization.transcriber import GeminiDiarizer
from telecom.settings import DEFAULT_DIARIZATION_INPUTS, INPUT_DIR

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diarização de falantes com Gemini (áudio inteiro, uma chamada)")
    parser.add_argument("--file", type=Path, help="Áudio ou vídeo de entrada. Padrão: arquivos preferidos em input/")
    parser.add_argument("--codec", choices=["opus", "mp3"], default="opus", help="Codec do áudio enviado (padrão: opus)")
    parser.add_argument("--vad", action="store_true", help="Remove pausas longas e remapeia os tempos ao original")
    parser.add_argument("--model", help="Modelo Gemini (padrão: GEMINI_MODEL ou gemini-2.5-flash)")
    args = parser.parse_args(argv)

    configure_logging()
    files = [args.file] if args.file else _default_inputs()
    if not files:
        logger.error("Nenhum arquivo em %s. Use --file.", INPUT_DIR)
        return 1

    diarizer = GeminiDiarizer(GeminiClient(model=args.model))
    pipeline = DiarizationPipeline(diarizer, DiarizationOptions(codec=args.codec, compact_silence=args.vad))
    for path in files:
        pipeline.run(path)
    return 0


def _default_inputs() -> list[Path]:
    preferred = [INPUT_DIR / name for name in DEFAULT_DIARIZATION_INPUTS if (INPUT_DIR / name).exists()]
    return preferred[:1] or media_in_input_dir()[:1]


if __name__ == "__main__":
    sys.exit(main())
