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
