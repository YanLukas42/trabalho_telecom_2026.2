"""Estratégias de codec: cada uma sabe os argumentos de encode do FFmpeg e o MIME type enviado à API."""

from abc import ABC, abstractmethod
from pathlib import Path


class AudioCodec(ABC):
    name: str
    extension: str
    mime_type: str

    @abstractmethod
    def encode_args(self, bitrate: str) -> list[str]:
        """Argumentos de saída do FFmpeg para este codec."""


class Mp3Codec(AudioCodec):
    name = "mp3"
    extension = ".mp3"
    mime_type = "audio/mp3"

    def encode_args(self, bitrate: str) -> list[str]:
        return ["-acodec", "libmp3lame", "-b:a", bitrate]


class OpusCodec(AudioCodec):
    """Opus em modo VoIP (SILK), VBR: otimizado para voz com pouca banda."""

    name = "opus"
    extension = ".opus"
    mime_type = "audio/ogg"

    def encode_args(self, bitrate: str) -> list[str]:
        return ["-acodec", "libopus", "-b:a", bitrate, "-vbr", "on", "-application", "voip"]


_CODECS: dict[str, AudioCodec] = {codec.name: codec for codec in (Mp3Codec(), OpusCodec())}


def get_codec(name: str) -> AudioCodec:
    try:
        return _CODECS[name.lower()]
    except KeyError as exc:
        raise ValueError(f"Codec desconhecido: {name!r}. Opções: {sorted(_CODECS)}") from exc


def mime_type_for_path(path: Path) -> str:
    """MIME type do arquivo, deduzido pela extensão, para o envio à API."""
    suffix = path.suffix.lower()
    if suffix in (".opus", ".ogg"):
        return OpusCodec.mime_type
    if suffix == ".wav":
        return "audio/wav"
    return Mp3Codec.mime_type
