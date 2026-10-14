import csv

from telecom.audio.filters import WIDEBAND_VOICE
from telecom.audio.preparer import Treatment
from telecom.benchmark.engine import BenchmarkEngine
from telecom.benchmark.report import write_benchmark_reports
from tests.conftest import requires_ffmpeg

TREATMENTS = (
    Treatment("base", "Base", "128k", 16000, 1, is_baseline=True),
    Treatment("band", "Banda", "32k", 16000, 1, filters=(WIDEBAND_VOICE,)),
)


@requires_ffmpeg
def test_dry_run_prepares_every_treatment_and_writes_reports(speech_wav, tmp_path):
    rows = BenchmarkEngine(TREATMENTS, output_dir=tmp_path / "audio").run(speech_wav)

    assert [row["treatment_id"] for row in rows] == ["base", "band"]
    assert all(row["processed_size_kb"] > 0 for row in rows)
    assert rows[1]["processed_size_kb"] < rows[0]["processed_size_kb"]
    assert all(row["wer"] is None for row in rows)  # sem transcrição não há o que medir

    paths = write_benchmark_reports(rows, speech_wav, tmp_path / "reports")
    with paths["csv"].open(encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2


class FixedTranscriber:
    def __init__(self, text_by_file):
        self._texts = text_by_file

    def transcribe(self, audio_path):
        from telecom.asr.gemini import GenerationResult

        return GenerationResult(self._texts[audio_path.stem.split("_")[-1]], 10, 5, 15, 0.2)


@requires_ffmpeg
def test_wer_is_measured_against_baseline_when_no_reference(speech_wav, tmp_path):
    transcriber = FixedTranscriber({"base": "um dois três", "band": "um dois quatro"})
    rows = BenchmarkEngine(TREATMENTS, output_dir=tmp_path / "audio", transcriber=transcriber).run(speech_wav)
    assert rows[0]["wer"] == 0.0
    assert rows[1]["wer"] == 33.33
