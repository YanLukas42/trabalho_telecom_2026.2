from telecom.diarization.models import Turn, WordTiming
from telecom.diarization.pyannote_whisper import PyannoteWhisperDiarizer
from tests.conftest import requires_ffmpeg


@requires_ffmpeg
def test_combines_pyannote_turns_with_whisper_words(speech_wav):
    turns = [Turn("SPEAKER_00", 0.0, 3.0), Turn("SPEAKER_01", 3.2, 6.0)]
    words = [
        WordTiming("bom", 0.2, 0.6), WordTiming("dia", 0.7, 1.1),
        WordTiming("obrigado", 3.4, 4.0),
    ]
    diarizer = PyannoteWhisperDiarizer(
        turn_source=lambda path: turns,
        word_source=lambda path: (words, "pt"),
    )

    result = diarizer.diarize(speech_wav)

    assert [(s.speaker, s.text) for s in result.segments] == [
        ("SPEAKER_00", "bom dia"),
        ("SPEAKER_01", "obrigado"),
    ]
    assert [w.speaker for w in result.words] == ["SPEAKER_00", "SPEAKER_00", "SPEAKER_01"]
    assert result.alignment["sem_falante"] == 0
    assert result.alignment["idioma"] == "pt"
    assert result.total_tokens == 0


@requires_ffmpeg
def test_warns_when_pyannote_returns_nothing(speech_wav):
    diarizer = PyannoteWhisperDiarizer(
        turn_source=lambda path: [],
        word_source=lambda path: ([WordTiming("oi", 0.1, 0.4)], "pt"),
    )
    result = diarizer.diarize(speech_wav)
    assert "pyannote não encontrou nenhum turno de fala" in result.alignment["avisos"]
    assert result.words[0].speaker == "desconhecido"
