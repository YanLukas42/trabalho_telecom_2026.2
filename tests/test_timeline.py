from telecom.diarization.models import Turn, WordTiming
from telecom.diarization.timeline import (
    UNKNOWN_SPEAKER,
    alignment_stats,
    alignment_warnings,
    assign_speakers,
    group_utterances,
)


def _w(text, start, end):
    return WordTiming(text, start, end)


TURNS = [Turn("SPEAKER_00", 0.0, 2.0), Turn("SPEAKER_01", 2.5, 5.0), Turn("SPEAKER_00", 5.2, 7.0)]


def test_word_takes_speaker_with_largest_overlap():
    labeled = assign_speakers([_w("oi", 1.8, 2.7)], TURNS)
    # 0.2 s com SPEAKER_00 e 0.2 s com SPEAKER_01: empate desfeito pelo primeiro de maior sobreposição
    assert labeled[0].speaker in {"SPEAKER_00", "SPEAKER_01"}


def test_word_inside_turn_gets_that_speaker():
    labeled = assign_speakers([_w("bom", 3.0, 3.4)], TURNS)
    assert labeled[0].speaker == "SPEAKER_01"


def test_word_in_gap_within_tolerance_gets_nearest_turn():
    # Termina a 0.1 s do fim do turno 0 e a 0.2 s do início do turno 1: vence o mais próximo.
    labeled = assign_speakers([_w("ok", 2.1, 2.3)], TURNS, tolerance_sec=0.3)
    assert labeled[0].speaker == "SPEAKER_00"


def test_word_far_from_any_turn_is_unknown():
    labeled = assign_speakers([_w("eh", 20.0, 20.4)], TURNS, tolerance_sec=0.3)
    assert labeled[0].speaker == UNKNOWN_SPEAKER


def test_turns_given_out_of_order_still_align():
    shuffled = [TURNS[2], TURNS[0], TURNS[1]]
    labeled = assign_speakers([_w("a", 0.5, 1.0), _w("b", 6.0, 6.5)], shuffled)
    assert [w.speaker for w in labeled] == ["SPEAKER_00", "SPEAKER_00"]


def test_group_splits_on_speaker_change_and_long_pause():
    labeled = assign_speakers(
        [_w("um", 0.1, 0.4), _w("dois", 0.5, 0.9), _w("três", 3.0, 3.4), _w("quatro", 3.5, 3.9)],
        TURNS,
    )
    segments = group_utterances(labeled, max_gap_sec=0.8)
    assert [s.speaker for s in segments] == ["SPEAKER_00", "SPEAKER_01"]
    assert segments[0].text == "um dois"
    assert segments[1].start_sec == 3.0 and segments[1].end_sec == 3.9


def test_unknown_word_joins_neighbour_speaker():
    labeled = assign_speakers([_w("a", 0.1, 0.4), _w("b", 9.0, 9.2), _w("c", 0.6, 0.9)], TURNS)
    segments = group_utterances(labeled)
    assert segments[0].speaker == "SPEAKER_00"


def test_stats_count_unknown_words():
    words = [_w("a", 0.1, 0.4), _w("b", 20.0, 20.4)]
    labeled = assign_speakers(words, TURNS)
    stats = alignment_stats(labeled, TURNS)
    assert stats["palavras"] == 2
    assert stats["sem_falante"] == 1
    assert stats["proporcao_sem_falante_pct"] == 50.0


def test_warnings_flag_words_past_end_of_audio():
    words = [_w("a", 0.1, 0.4), _w("b", 90.0, 90.4)]
    labeled = assign_speakers(words, TURNS)
    warnings = alignment_warnings(labeled, TURNS, duration_sec=10.0)
    assert any("depois do fim do áudio" in w for w in warnings)


def test_warnings_when_pyannote_finds_no_turns():
    warnings = alignment_warnings([], [], duration_sec=10.0)
    assert warnings == ["pyannote não encontrou nenhum turno de fala"]
