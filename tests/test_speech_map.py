from telecom.audio.silence import Interval
from telecom.audio.vad import SpeechMap, SpeechSegment, compact_pcm


def _map(*segments):
    return SpeechMap(tuple(segments), original_duration=110.0, compact_duration=65.0)


def test_to_original_maps_inside_each_block():
    speech = _map(
        SpeechSegment(10.0, 25.0, 0.0, 15.0, 15.0),
        SpeechSegment(40.0, 70.0, 15.0, 45.0, 30.0),
        SpeechSegment(90.0, 110.0, 45.0, 65.0, 20.0),
    )
    assert speech.to_original(0.0) == 10.0
    assert speech.to_original(5.0) == 15.0
    assert speech.to_original(20.0) == 45.0  # bloco 2: 40 + (20 - 15)
    assert speech.to_original(50.0) == 95.0  # bloco 3: 90 + (50 - 45)


def test_to_original_clamps_at_edges():
    speech = _map(
        SpeechSegment(10.0, 25.0, 0.0, 15.0, 15.0),
        SpeechSegment(40.0, 70.0, 15.0, 45.0, 30.0),
    )
    assert speech.to_original(50.0) == 70.0
    assert speech.to_original(-1.0) == 10.0


def test_to_original_without_segments_is_identity():
    assert SpeechMap((), 10.0, 10.0).to_original(12.5) == 12.5


def test_from_silences_removes_pauses_and_keeps_speech_order():
    silences = [Interval(10.0, 14.0), Interval(30.0, 36.0)]
    speech = SpeechMap.from_silences(silences, duration=50.0, pad_sec=0.1)

    assert [round(s.orig_start, 2) for s in speech.segments] == [0.0, 14.0 - 0.1, 36.0 - 0.1]
    assert speech.compact_duration < speech.original_duration
    assert speech.saved_sec == round(50.0 - speech.compact_duration, 2)
    # Os trechos compactados são contíguos e começam em zero.
    assert speech.segments[0].comp_start == 0.0
    assert speech.segments[1].comp_start == speech.segments[0].comp_end


def test_from_silences_without_silence_is_one_block():
    speech = SpeechMap.from_silences([], duration=20.0)
    assert len(speech.segments) == 1
    assert speech.segments[0].orig_end == 20.0
    assert speech.saved_pct == 0.0


def test_overlapping_padding_is_merged():
    # Pausa curta entre dois trechos: com margem, os trechos se fundem em um só.
    speech = SpeechMap.from_silences([Interval(5.0, 5.5)], duration=10.0, pad_sec=0.4)
    assert len(speech.segments) == 1


def test_compact_pcm_concatenates_speech_samples():
    sample_rate, channels = 10, 1  # 10 amostras por segundo, 2 bytes cada
    pcm = bytes(range(200)) * 1  # 20 s de áudio
    speech = SpeechMap(
        (
            SpeechSegment(0.0, 1.0, 0.0, 1.0, 1.0),
            SpeechSegment(5.0, 6.0, 1.0, 2.0, 1.0),
        ),
        original_duration=20.0,
        compact_duration=2.0,
    )
    compact = compact_pcm(pcm, speech, sample_rate, channels)
    assert len(compact) == 2 * sample_rate * 2
    assert compact == pcm[0:20] + pcm[100:120]


def test_to_dicts_keeps_serialized_keys():
    speech = SpeechMap((SpeechSegment(0.0, 1.0, 0.0, 1.0, 1.0),), 2.0, 1.0)
    assert speech.to_dicts() == [
        {"orig_start": 0.0, "orig_end": 1.0, "comp_start": 0.0, "comp_end": 1.0, "duration": 1.0}
    ]
