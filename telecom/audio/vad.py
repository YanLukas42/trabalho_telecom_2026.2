"""VAD por mapa de tempo: remove pausas longas e guarda como voltar ao instante do áudio original."""

from dataclasses import dataclass
from pathlib import Path

from telecom.audio.ffmpeg import probe_duration
from telecom.audio.silence import Interval, detect_silences

DEFAULT_NOISE_DB = -35.0
DEFAULT_MIN_SILENCE_SEC = 0.4
DEFAULT_PAD_SEC = 0.10

# Trechos menores que isso são ruído de borda e são descartados.
_MIN_EDGE_SEC = 0.05


@dataclass(frozen=True)
class SpeechSegment:
    """Um trecho de fala: onde está no original e onde cai no áudio compactado."""

    orig_start: float
    orig_end: float
    comp_start: float
    comp_end: float
    duration: float


@dataclass(frozen=True)
class SpeechMap:
    segments: tuple[SpeechSegment, ...]
    original_duration: float
    compact_duration: float

    @classmethod
    def from_silences(cls, silences: list[Interval], duration: float, pad_sec: float = DEFAULT_PAD_SEC) -> "SpeechMap":
        """Constrói o mapa a partir dos silêncios detectados (função pura, testável sem FFmpeg)."""
        spans = _speech_spans(silences, duration)
        padded = _pad_and_merge(spans, duration, pad_sec)

        segments: list[SpeechSegment] = []
        comp_pos = 0.0
        for start, end in padded:
            seg_duration = round(end - start, 3)
            if seg_duration <= _MIN_EDGE_SEC:
                continue
            comp_start = round(comp_pos, 3)
            comp_end = round(comp_pos + seg_duration, 3)
            segments.append(SpeechSegment(round(start, 3), round(end, 3), comp_start, comp_end, seg_duration))
            comp_pos = comp_end

        return cls(tuple(segments), original_duration=duration, compact_duration=round(comp_pos, 3))

    def to_original(self, t_compact: float) -> float:
        """Converte um instante do áudio compactado para o instante correspondente no original."""
        if not self.segments:
            return t_compact

        for seg in self.segments:
            if seg.comp_start <= t_compact <= seg.comp_end:
                return round(seg.orig_start + (t_compact - seg.comp_start), 2)

        # Arredondamento nas bordas do áudio compactado.
        if t_compact >= self.segments[-1].comp_end:
            return self.segments[-1].orig_end
        if t_compact < self.segments[0].comp_start:
            return self.segments[0].orig_start
        return t_compact

    @property
    def saved_sec(self) -> float:
        return round(max(0.0, self.original_duration - self.compact_duration), 2)

    @property
    def saved_pct(self) -> float:
        if self.original_duration <= 0:
            return 0.0
        return round(self.saved_sec / self.original_duration * 100.0, 2)

    def to_dicts(self) -> list[dict]:
        """Forma serializável, gravada no JSON de diarização."""
        return [
            {
                "orig_start": seg.orig_start,
                "orig_end": seg.orig_end,
                "comp_start": seg.comp_start,
                "comp_end": seg.comp_end,
                "duration": seg.duration,
            }
            for seg in self.segments
        ]


def build_speech_map(
    path: Path,
    noise_db: float = DEFAULT_NOISE_DB,
    min_silence_sec: float = DEFAULT_MIN_SILENCE_SEC,
    pad_sec: float = DEFAULT_PAD_SEC,
) -> SpeechMap:
    duration = probe_duration(path)
    silences = detect_silences(path, noise_db=noise_db, min_sec=min_silence_sec)
    return SpeechMap.from_silences(silences, duration, pad_sec=pad_sec)


def compact_pcm(pcm: bytes, speech_map: SpeechMap, sample_rate: int, channels: int) -> bytes:
    """Concatena apenas os trechos de fala do PCM bruto, com precisão de amostra."""
    frame_size = channels * 2  # s16le: 2 bytes por amostra
    pieces = []
    for seg in speech_map.segments:
        start = min(len(pcm), max(0, round(seg.orig_start * sample_rate) * frame_size))
        end = min(len(pcm), max(0, round(seg.orig_end * sample_rate) * frame_size))
        pieces.append(pcm[start:end])
    return b"".join(pieces) if pieces else pcm


def _speech_spans(silences: list[Interval], duration: float) -> list[tuple[float, float]]:
    """Os intervalos entre os silêncios são fala."""
    if not silences:
        return [(0.0, duration)]

    spans: list[tuple[float, float]] = []
    if silences[0].start > _MIN_EDGE_SEC:
        spans.append((0.0, silences[0].start))
    for prev, nxt in zip(silences, silences[1:]):
        if nxt.start - prev.end > _MIN_EDGE_SEC:
            spans.append((prev.end, nxt.start))
    if silences[-1].end < duration - _MIN_EDGE_SEC:
        spans.append((silences[-1].end, duration))
    return spans


def _pad_and_merge(spans: list[tuple[float, float]], duration: float, pad_sec: float) -> list[tuple[float, float]]:
    """Adiciona margem em cada trecho para não cortar bordas de palavras, e funde os que se sobrepõem."""
    merged: list[tuple[float, float]] = []
    for start, end in spans:
        p_start = max(0.0, start - pad_sec)
        p_end = min(duration, end + pad_sec)
        if merged and p_start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(p_end, merged[-1][1]))
        else:
            merged.append((p_start, p_end))
    return merged
