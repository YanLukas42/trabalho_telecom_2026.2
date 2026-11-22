import io

import pytest

from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline
from telecom.web.jobs import JobOptions, JobService, JobStatus, UNEXPECTED_ERROR_MESSAGE, sanitize_filename
from tests.conftest import requires_ffmpeg
from tests.test_pipeline import FakeDiarizer


class ImmediateExecutor:
    """Roda o job na hora, na mesma thread: o teste não precisa esperar."""

    def submit(self, fn, *args):
        fn(*args)


def fake_factory(options, output_dir):
    return DiarizationPipeline(FakeDiarizer(), DiarizationOptions(compact_silence=options.compact_silence), output_dir)


def failing_factory(error):
    def factory(options, output_dir):
        raise error
    return factory


def test_sanitize_filename_strips_paths_and_odd_chars():
    assert sanitize_filename("../../etc/aula de hoje.mp3") == "aula_de_hoje.mp3"
    assert sanitize_filename("C:\\fakepath\\áudio.wav".split("\\")[-1]) == "áudio.wav"
    with pytest.raises(ValueError):
        sanitize_filename("...")


def test_rejects_unsupported_extension(tmp_path):
    service = JobService(fake_factory, tmp_path, ImmediateExecutor())
    with pytest.raises(ValueError, match="Formato não suportado"):
        service.submit("notas.txt", io.BytesIO(b"x"), JobOptions())
    assert service.list() == []


def test_rejects_empty_file_and_cleans_up(tmp_path):
    service = JobService(fake_factory, tmp_path, ImmediateExecutor())
    with pytest.raises(ValueError, match="vazio"):
        service.submit("aula.mp3", io.BytesIO(b""), JobOptions())
    assert list(tmp_path.iterdir()) == []


@requires_ffmpeg
def test_job_runs_pipeline_and_keeps_outputs(speech_wav, tmp_path):
    service = JobService(fake_factory, tmp_path / "jobs", ImmediateExecutor())
    with speech_wav.open("rb") as handle:
        job = service.submit("speech.wav", handle, JobOptions(compact_silence=True))

    assert job.status is JobStatus.DONE
    assert job.source == tmp_path / "jobs" / job.id / "upload" / "speech.wav"
    assert job.outputs.report_json.is_relative_to(tmp_path / "jobs" / job.id)
    assert job.outputs.payload["vad_aplicado"] is True
    assert job.finished_at >= job.started_at


def test_known_errors_keep_their_message(tmp_path):
    service = JobService(failing_factory(ValueError("Arquivo grande demais")), tmp_path, ImmediateExecutor())
    job = service.submit("aula.mp3", io.BytesIO(b"abc"), JobOptions())
    assert job.status is JobStatus.FAILED
    assert job.error == "Arquivo grande demais"


def test_unexpected_errors_are_hidden_from_the_user(tmp_path):
    service = JobService(failing_factory(RuntimeError("stack interna")), tmp_path, ImmediateExecutor())
    job = service.submit("aula.mp3", io.BytesIO(b"abc"), JobOptions())
    assert job.status is JobStatus.FAILED
    assert job.error == UNEXPECTED_ERROR_MESSAGE


def test_list_is_newest_first(tmp_path):
    service = JobService(failing_factory(ValueError("x")), tmp_path, ImmediateExecutor())
    first = service.submit("a.mp3", io.BytesIO(b"1"), JobOptions())
    second = service.submit("b.mp3", io.BytesIO(b"2"), JobOptions())
    assert [job.id for job in service.list()] == [second.id, first.id]
