"""CLI de diarização. Uso: python -m telecom.cli.diarize [--engine pyannote|gemini] [--file ARQ] [--vad] [--review]"""

import argparse
import logging
import sys
from pathlib import Path

from telecom.asr.gemini import GeminiClient
from telecom.cli.common import configure_logging, media_in_input_dir
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.diarization.review import GeminiReviewer
from telecom.settings import DEFAULT_DIARIZATION_INPUTS, HF_TOKEN, INPUT_DIR

logger = logging.getLogger(__name__)

DEFAULT_CODEC = {"pyannote": "wav", "gemini": "opus"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diarização de falantes: pyannote + whisper, ou Gemini")
    parser.add_argument("--engine", choices=["pyannote", "gemini"], default="pyannote",
                        help="pyannote: local (pyannote + whisper). gemini: áudio inteiro na API")
    parser.add_argument("--file", type=Path, help="Áudio ou vídeo de entrada. Padrão: arquivos preferidos em input/")
    parser.add_argument("--codec", choices=["wav", "opus", "mp3"], default=None,
                        help="Padrão: wav (pyannote) ou opus (gemini)")
    parser.add_argument("--vad", action="store_true", help="Remove pausas longas e remapeia os tempos ao original")
    parser.add_argument("--review", action="store_true",
                        help="IA (Gemini, só texto) sugere nomes dos falantes e aponta possíveis erros")
    parser.add_argument("--whisper-model", default="small", help="Modelo do faster-whisper (padrão: small)")
    parser.add_argument("--language", default="pt", help="Idioma da transcrição (padrão: pt)")
    parser.add_argument("--device", default="cpu", help="cpu ou cuda")
    parser.add_argument("--num-speakers", type=int, help="Número exato de falantes, se souber")
    parser.add_argument("--min-speakers", type=int)
    parser.add_argument("--max-speakers", type=int)
    parser.add_argument("--model", help="Modelo Gemini (padrão: GEMINI_MODEL ou gemini-2.5-flash)")
    args = parser.parse_args(argv)

    configure_logging()
    files = [args.file] if args.file else _default_inputs()
    if not files:
        logger.error("Nenhum arquivo em %s. Use --file.", INPUT_DIR)
        return 1

    diarizer = _build_diarizer(args)
    codec = args.codec or DEFAULT_CODEC[args.engine]
    reviewer = GeminiReviewer(GeminiClient(model=args.model)) if args.review else None
    pipeline = DiarizationPipeline(
        diarizer,
        DiarizationOptions(codec=codec, compact_silence=args.vad),
        reviewer=reviewer,
    )
    for path in files:
        pipeline.run(path)
    return 0


def _build_diarizer(args: argparse.Namespace):
    if args.engine == "gemini":
        from telecom.diarization.transcriber import GeminiDiarizer

        return GeminiDiarizer(GeminiClient(model=args.model))

    if not HF_TOKEN:
        raise SystemExit("HF_TOKEN não configurado no .env. O modelo do pyannote é restrito no Hugging Face.")

    from telecom.diarization.pyannote_whisper import build_local_diarizer

    return build_local_diarizer(
        hf_token=HF_TOKEN,
        whisper_model=args.whisper_model,
        device=args.device,
        language=args.language,
        num_speakers=args.num_speakers,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
    )


def _default_inputs() -> list[Path]:
    preferred = [INPUT_DIR / name for name in DEFAULT_DIARIZATION_INPUTS if (INPUT_DIR / name).exists()]
    return preferred[:1] or media_in_input_dir()[:1]


if __name__ == "__main__":
    sys.exit(main())
