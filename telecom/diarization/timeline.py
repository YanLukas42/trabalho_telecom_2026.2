"""Alinhamento entre turnos do pyannote e palavras do whisper. Funções puras, testáveis sem os modelos."""

from bisect import bisect_left, bisect_right
from typing import Any, Sequence

from telecom.diarization.models import SpeakerSegment, SpeakerWord, Turn, WordTiming

UNKNOWN_SPEAKER = "desconhecido"
# Acima desta fração de palavras sem falante, o alinhamento provavelmente está deslocado.
UNKNOWN_WARN_PCT = 10.0
# Palavra que termina depois do fim do áudio por mais que isso indica deslocamento de tempo.
END_TOLERANCE_SEC = 1.0


def assign_speakers(
    words: Sequence[WordTiming],
    turns: Sequence[Turn],
    tolerance_sec: float = 0.3,
) -> list[SpeakerWord]:
    """Cada palavra recebe o falante do turno com maior sobreposição de tempo.

    Sem sobreposição, recebe o turno mais próximo dentro de `tolerance_sec`. Caso contrário, UNKNOWN_SPEAKER.
    """
    ordered = sorted(turns, key=lambda turn: turn.start)
    starts = [turn.start for turn in ordered]
    # Maior fim visto até cada índice: não decresce, então permite busca binária.
    reach: list[float] = []
    running_end = float("-inf")
    for turn in ordered:
        running_end = max(running_end, turn.end)
        reach.append(running_end)

    labeled: list[SpeakerWord] = []
    for word in words:
        low = bisect_left(reach, word.start - tolerance_sec)
        high = bisect_right(starts, word.end + tolerance_sec)
        turn = _turn_for(word, ordered[low:high], tolerance_sec)
        speaker = turn.speaker if turn is not None else UNKNOWN_SPEAKER
        labeled.append(SpeakerWord(word.text, word.start, word.end, speaker))
    return labeled


def _turn_for(word: WordTiming, candidates: Sequence[Turn], tolerance_sec: float) -> Turn | None:
    best: Turn | None = None
    best_overlap = 0.0
    nearest: Turn | None = None
    nearest_gap = tolerance_sec
    for turn in candidates:
        overlap = min(word.end, turn.end) - max(word.start, turn.start)
        if overlap > best_overlap:
            best, best_overlap = turn, overlap
        gap = max(turn.start - word.end, word.start - turn.end, 0.0)
        if gap <= nearest_gap:
            nearest, nearest_gap = turn, gap
    return best if best is not None else nearest


def group_utterances(words: Sequence[SpeakerWord], max_gap_sec: float = 0.8) -> list[SpeakerSegment]:
    """Agrupa palavras consecutivas do mesmo falante, separando por troca de falante ou pausa longa."""
    groups: list[list[SpeakerWord]] = []
    for word in words:
        if groups and _continues(groups[-1][-1], word, max_gap_sec):
            groups[-1].append(word)
        else:
            groups.append([word])

    return [
        SpeakerSegment(
            speaker=_group_speaker(group),
            text=" ".join(word.text for word in group),
            start_sec=group[0].start,
            end_sec=group[-1].end,
        )
        for group in groups
    ]


def alignment_stats(words: Sequence[SpeakerWord], turns: Sequence[Turn]) -> dict[str, Any]:
    total = len(words)
    unknown = sum(1 for word in words if word.speaker == UNKNOWN_SPEAKER)
    return {
        "palavras": total,
        "sem_falante": unknown,
        "proporcao_sem_falante_pct": round(unknown / total * 100.0, 2) if total else 0.0,
        "turnos_pyannote": len(turns),
    }


def alignment_warnings(words: Sequence[SpeakerWord], turns: Sequence[Turn], duration_sec: float) -> list[str]:
    warnings: list[str] = []
    if not turns:
        warnings.append("pyannote não encontrou nenhum turno de fala")
    if words:
        last_end = max(word.end for word in words)
        if last_end > duration_sec + END_TOLERANCE_SEC:
            warnings.append(
                f"há palavras até {last_end:.1f}s, depois do fim do áudio ({duration_sec:.1f}s): "
                "os tempos do whisper e do pyannote podem estar deslocados"
            )
        unknown_pct = alignment_stats(words, turns)["proporcao_sem_falante_pct"]
        if unknown_pct > UNKNOWN_WARN_PCT:
            warnings.append(
                f"{unknown_pct}% das palavras ficaram sem falante: "
                "provável deslocamento entre a segmentação do pyannote e a do whisper"
            )
    return warnings


def _continues(last: SpeakerWord, word: SpeakerWord, max_gap_sec: float) -> bool:
    if word.start - last.end > max_gap_sec:
        return False
    return (
        word.speaker == last.speaker
        or word.speaker == UNKNOWN_SPEAKER
        or last.speaker == UNKNOWN_SPEAKER
    )


def _group_speaker(group: Sequence[SpeakerWord]) -> str:
    return next((word.speaker for word in group if word.speaker != UNKNOWN_SPEAKER), UNKNOWN_SPEAKER)
