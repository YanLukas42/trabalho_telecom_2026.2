"""Utilitários compartilhados pelas CLIs: logging e descoberta de arquivos de entrada."""

import logging
from pathlib import Path

from telecom.settings import INPUT_DIR, MEDIA_EXTENSIONS


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def media_in_input_dir(directory: Path = INPUT_DIR) -> list[Path]:
    """Mídias da pasta de entrada, em ordem estável."""
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS and not path.name.startswith(".")
    )
