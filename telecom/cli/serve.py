"""Servidor web local. Uso: python -m telecom.cli.serve [--host 127.0.0.1] [--port 8000]

Composition root: aqui o pipeline real é montado e injetado na aplicação web.
"""

import argparse
import logging
import sys
from pathlib import Path

import uvicorn

from telecom.asr.gemini import GeminiClient
from telecom.cli.common import configure_logging
from telecom.diarization.factory import DEFAULT_CODEC, build_diarizer, engine_unavailable_reason
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.diarization.prompts import build_class_prompt
from telecom.diarization.review import GeminiReviewer
from telecom.lessons.materials import GeminiLessonWriter, LessonWriter
from telecom.web.app import create_app
from telecom.web.jobs import JobOptions, JobService

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
# Aulas de inglês: o Whisper local transcreve em inglês; o Gemini recebe o prompt de aula.
CLASS_LANGUAGE = "en"


def build_lesson_writer() -> LessonWriter:
    return GeminiLessonWriter(GeminiClient())


def build_pipeline(options: JobOptions, output_dir: Path) -> DiarizationPipeline:
    reviewer = GeminiReviewer(GeminiClient()) if options.review else None
    return DiarizationPipeline(
        build_diarizer(options.engine, language=CLASS_LANGUAGE, prompt=build_class_prompt()),
        DiarizationOptions(codec=DEFAULT_CODEC[options.engine], compact_silence=options.compact_silence),
        output_dir=output_dir,
        reviewer=reviewer,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interface web de transcrição e diarização")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)

    configure_logging()
    app = create_app(JobService(build_pipeline), engine_unavailable_reason, build_lesson_writer)
    logger.info("Abra http://%s:%d no navegador", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
