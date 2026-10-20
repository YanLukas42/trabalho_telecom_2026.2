import json

from telecom.diarization.models import SpeakerSegment, Transcription
from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from tests.conftest import requires_ffmpeg


class FakeDiarizer:
    """Diarizador determinístico: registra as chamadas e não usa a API."""

    def __init__(self):
        self.calls = []

    def diarize(self, audio_path):
        self.calls.append(audio_path)
        return Transcription(
            segments=(
                SpeakerSegment("Juiz", "Olá.", 0.5, 4.0),
                SpeakerSegment("Réu / Bruno", "Oi.", 5.0, 9.0),
            ),
            prompt_tokens=100,
            candidate_tokens=50,
            total_tokens=150,
            latency_sec=0.1,
        )


@requires_ffmpeg
def test_vad_maps_timeline_back_to_original(speech_wav, tmp_path):
    diarizer = FakeDiarizer()
    outputs = DiarizationPipeline(diarizer, DiarizationOptions(compact_silence=True), tmp_path / "out").run(speech_wav)

    assert outputs.report_json.name == "speech_diarizacao_pydantic_vad.json"
    assert outputs.words_json.name == "speech_palavra_por_palavra_vad.json"
    assert len(diarizer.calls) == 1
    assert diarizer.calls[0].name.endswith("_vad_compact.opus")

    payload = json.loads(outputs.report_json.read_text(encoding="utf-8"))
    assert payload["vad_aplicado"] is True
    assert payload["duracao_compactada_segundos"] < payload["duracao_original_segundos"]
    assert payload["vad_segments_map"]
    for segment in payload["segmentos"]:
        assert segment["segundos_inicio"] <= segment["segundos_fim"] <= payload["duracao_original_segundos"]
        assert "segundos_inicio_compact" in segment


@requires_ffmpeg
def test_without_vad_keeps_times_and_sends_one_file(speech_wav, tmp_path):
    diarizer = FakeDiarizer()
    outputs = DiarizationPipeline(diarizer, DiarizationOptions(compact_silence=False), tmp_path / "out").run(speech_wav)

    assert len(diarizer.calls) == 1
    assert diarizer.calls[0].name.endswith("_optimized.opus")
    payload = json.loads(outputs.report_json.read_text(encoding="utf-8"))
    assert payload["vad_aplicado"] is False
    assert "vad_segments_map" not in payload
    assert payload["economia_silencio_segundos"] == 0.0
    assert payload["total_turnos_fala"] == 2
    assert payload["segmentos"][0]["timestamp"] == "00:00 - 00:04"


class WordsDiarizer:
    """Como o pyannote+whisper: devolve palavras com tempo e falante."""

    def diarize(self, audio_path):
        from telecom.diarization.models import SpeakerWord

        words = (SpeakerWord("bom", 0.5, 1.0, "SPEAKER_00"), SpeakerWord("dia", 1.1, 1.6, "SPEAKER_00"),
                 SpeakerWord("oi", 5.0, 5.4, "SPEAKER_01"))
        segments = (SpeakerSegment("SPEAKER_00", "bom dia", 0.5, 1.6), SpeakerSegment("SPEAKER_01", "oi", 5.0, 5.4))
        return Transcription(segments, 0, 0, 0, 0.0, words=words, alignment={"palavras": 3})


class FakeReviewer:
    def review(self, segments):
        from telecom.diarization.review import FalanteIdentificado, RevisaoTranscricao

        return RevisaoTranscricao(
            falantes=[FalanteIdentificado(rotulo="SPEAKER_00", nome="Dr. Carlos", confianca=0.9,
                                          evidencia="bom dia")],
            revisoes=[],
        )


@requires_ffmpeg
def test_words_come_from_transcriber_and_names_from_review(speech_wav, tmp_path):
    outputs = DiarizationPipeline(
        WordsDiarizer(), DiarizationOptions(codec="wav"), tmp_path / "out", reviewer=FakeReviewer()
    ).run(speech_wav)

    words = json.loads(outputs.words_json.read_text(encoding="utf-8"))
    assert [(w["palavra"], w["segundos_inicio"], w["quemfala"]) for w in words["palavras"]] == [
        ("bom", 0.5, "SPEAKER_00"), ("dia", 1.1, "SPEAKER_00"), ("oi", 5.0, "SPEAKER_01"),
    ]

    payload = json.loads(outputs.report_json.read_text(encoding="utf-8"))
    assert payload["segmentos"][0]["falante_identificado"] == "Dr. Carlos"
    assert payload["segmentos"][1]["falante_identificado"] is None
    assert payload["revisao"]["nomes_aplicados"] == {"SPEAKER_00": "Dr. Carlos"}
    assert payload["alinhamento"] == {"palavras": 3}
    assert "Dr. Carlos (SPEAKER_00)" in outputs.report_md.read_text(encoding="utf-8")


@requires_ffmpeg
def test_word_times_are_mapped_back_to_original_with_vad(speech_wav, tmp_path):
    outputs = DiarizationPipeline(
        WordsDiarizer(), DiarizationOptions(codec="wav", compact_silence=True), tmp_path / "out"
    ).run(speech_wav)
    payload = json.loads(outputs.report_json.read_text(encoding="utf-8"))
    words = json.loads(outputs.words_json.read_text(encoding="utf-8"))
    assert payload["vad_aplicado"] is True
    assert all(w["segundos_fim"] <= payload["duracao_original_segundos"] for w in words["palavras"])
