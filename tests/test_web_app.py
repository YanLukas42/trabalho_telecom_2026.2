import pytest
from fastapi.testclient import TestClient

from telecom.lessons.materials import LessonMaterials, validated_materials
from telecom.web.app import create_app
from telecom.web.jobs import JobService
from tests.conftest import requires_ffmpeg
from tests.test_web_jobs import ImmediateExecutor, fake_factory


def only_gemini(engine):
    return None if engine == "gemini" else "HF_TOKEN não configurado no .env."


@pytest.fixture
def client(tmp_path):
    service = JobService(fake_factory, tmp_path / "jobs", ImmediateExecutor())
    return TestClient(create_app(service, only_gemini))


def test_config_reports_engine_availability(client):
    body = client.get("/api/config").json()
    engines = {engine["id"]: engine for engine in body["engines"]}
    assert engines["gemini"]["available"] is True
    assert engines["pyannote"]["available"] is False
    assert engines["pyannote"]["unavailable_reason"].startswith("HF_TOKEN")
    assert body["review_available"] is True
    assert ".mp4" in body["extensions"]


def test_serves_the_interface(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Pauta" in response.text


def test_unavailable_engine_is_rejected(client):
    response = client.post("/api/jobs", data={"engine": "pyannote"}, files={"file": ("a.mp3", b"abc")})
    assert response.status_code == 400
    assert "HF_TOKEN" in response.json()["detail"]


def test_bad_extension_is_rejected(client):
    response = client.post("/api/jobs", files={"file": ("notas.txt", b"abc")})
    assert response.status_code == 400


def test_unknown_job_is_404(client):
    assert client.get("/api/jobs/nao-existe").status_code == 404
    assert client.get("/api/jobs/nao-existe/files/md").status_code == 404


class FakeLessonWriter:
    def __init__(self):
        self.requests = []

    def write(self, segments, request):
        self.requests.append((segments, request))
        return validated_materials(LessonMaterials.model_validate({
            "students": [{
                "speaker": "Réu / Bruno",
                "strength": "Responde rápido.",
                "mistakes": [{"quote": "Oi", "correction": "Hi", "explanation": "Em inglês."}],
                "exercises": [{"kind": "short_answer", "prompt": "Greet someone.", "options": [], "answer": "Hi!"}],
            }],
            "plan": {"objective": "Cumprimentos.", "topics": [], "blocks": [], "homework": "Nenhuma."},
        }), request, segments)


@pytest.fixture
def lesson_client(tmp_path):
    writer = FakeLessonWriter()
    service = JobService(fake_factory, tmp_path / "jobs", ImmediateExecutor())
    return TestClient(create_app(service, only_gemini, lambda: writer)), writer, tmp_path


def lesson_body(**changes):
    return {
        "level": "A2",
        "participants": [
            {"label": "Juiz", "name": "Rafael", "role": "teacher"},
            {"label": "Réu / Bruno", "name": "Bruno", "role": "student"},
        ],
        **changes,
    }


def upload(client, speech_wav):
    response = client.post("/api/jobs", files={"file": ("speech.wav", speech_wav.read_bytes(), "audio/wav")})
    return response.json()["id"]


def test_config_exposes_lesson_settings(lesson_client):
    body = lesson_client[0].get("/api/config").json()
    assert body["lessons_available"] is True
    assert body["levels"][0] == "A1"
    assert body["min_exercises"] < body["default_exercises"] <= body["max_exercises"]


def test_lessons_unavailable_without_a_writer(client):
    assert client.get("/api/config").json()["lessons_available"] is False


def test_lesson_for_unknown_job_is_404(lesson_client):
    assert lesson_client[0].post("/api/jobs/nao-existe/lesson", json=lesson_body()).status_code == 404


@requires_ffmpeg
def test_lesson_is_generated_saved_and_returned_with_the_job(lesson_client, speech_wav):
    client, writer, tmp_path = lesson_client
    job_id = upload(client, speech_wav)

    response = client.post(f"/api/jobs/{job_id}/lesson", json=lesson_body(focus="greetings"))
    assert response.status_code == 200
    assert response.json()["lesson"]["students"][0]["speaker"] == "Réu / Bruno"
    assert writer.requests[0][1].focus == "greetings"
    assert (tmp_path / "jobs" / job_id / "lesson.json").exists()

    assert client.get(f"/api/jobs/{job_id}").json()["lesson"]["plan"]["objective"] == "Cumprimentos."
    assert client.get("/api/jobs").json()[0]["lesson"] is None


@requires_ffmpeg
def test_lesson_rejects_invalid_requests_with_a_readable_message(lesson_client, speech_wav):
    client, _, _ = lesson_client
    job_id = upload(client, speech_wav)

    no_student = lesson_body(participants=[{"label": "Juiz", "name": "Rafael", "role": "teacher"}])
    response = client.post(f"/api/jobs/{job_id}/lesson", json=no_student)
    assert response.status_code == 400
    assert "aluno" in response.json()["detail"]

    assert client.post(f"/api/jobs/{job_id}/lesson", json=lesson_body(level="Z9")).status_code == 400


@requires_ffmpeg
def test_full_flow_upload_result_and_downloads(client, speech_wav):
    response = client.post(
        "/api/jobs",
        data={"engine": "gemini", "compact_silence": "true"},
        files={"file": ("speech.wav", speech_wav.read_bytes(), "audio/wav")},
    )
    assert response.status_code == 202
    job_id = response.json()["id"]

    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "done"
    assert job["compact_silence"] is True
    assert job["result"]["total_turnos_fala"] == 2
    assert job["result"]["segmentos"][0]["quemfala"] == "Juiz"

    listed = client.get("/api/jobs").json()
    assert [item["id"] for item in listed] == [job_id]
    assert listed[0]["result"] is None

    markdown = client.get(f"/api/jobs/{job_id}/files/md")
    assert markdown.status_code == 200
    assert "Juiz" in markdown.text
    assert client.get(f"/api/jobs/{job_id}/files/words").json()["total_palavras"] > 0
    assert client.get(f"/api/jobs/{job_id}/files/outro").status_code == 404
    assert client.get(f"/api/jobs/{job_id}/media").status_code == 200
