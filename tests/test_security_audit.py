import asyncio
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from telecom.audio.ffmpeg import FFMPEG_TIMEOUT_SEC, FFPROBE_TIMEOUT_SEC, FFmpegError, probe_duration, run_ffmpeg
from telecom.diarization.models import SpeakerSegment
from telecom.diarization.review import FalanteIdentificado, RevisaoTranscricao, identified_names
from telecom.lessons.materials import LessonMaterials, LessonPlan, LessonRequest, Participant, StudentSheet, validated_materials
from telecom.web.app import SECURITY_HEADERS, STATIC_DIR, SecurityHeadersMiddleware


# --- Item 1: Sem dados pessoais em logs ---

def test_logs_do_not_contain_student_speech(caplog):
    caplog.set_level(logging.INFO)
    request = LessonRequest(
        level="A1",
        participants=(Participant("A1", "Carlos", "student"),),
        exercises_per_student=3,
    )
    # Fala do aluno tem "hello", mas o erro inventado cita "nonexistent text"
    segments = [SpeakerSegment(speaker="A1", text="hello world", start_sec=0.0, end_sec=1.0)]
    materials = LessonMaterials(
        students=[StudentSheet(
            speaker="A1",
            strength="Bom vocabulário",
            mistakes=[{"quote": "nonexistent secret speech of student", "correction": "fix", "explanation": "exp"}],
            exercises=[{"kind": "short_answer", "prompt": "p", "options": [], "answer": "a"}] * 3,
        )],
        plan=LessonPlan(objective="Obj", topics=[], blocks=[], homework=""),
    )

    validated_materials(materials, request, segments)

    # Garante que a fala "nonexistent secret speech of student" NÃO foi para os logs
    log_text = caplog.text
    assert "nonexistent secret speech of student" not in log_text
    assert "Erro descartado para o participante A1" in log_text


def test_logs_do_not_contain_personal_names(caplog):
    caplog.set_level(logging.INFO)
    review = RevisaoTranscricao(
        falantes=[
            FalanteIdentificado(rotulo="F1", nome="Carlos Alberto Silva", confianca=0.2, evidencia="Carlos"),
            FalanteIdentificado(rotulo="F2", nome="Maria Eduarda Santos", confianca=0.9, evidencia="sem evidencia no texto"),
        ],
        revisoes=[],
    )
    segments = [SpeakerSegment(speaker="F1", text="olá mundo", start_sec=0, end_sec=1)]

    identified_names(review, segments)

    log_text = caplog.text
    assert "Carlos Alberto Silva" not in log_text
    assert "Maria Eduarda Santos" not in log_text
    assert "Nome descartado para o rótulo F1 por confiança insuficiente" in log_text
    assert "Nome descartado para o rótulo F2 por evidência ausente no texto" in log_text


# --- Item 2: FFmpeg/FFprobe com timeout e protocol_whitelist ---

def test_ffmpeg_protocol_whitelist_and_timeout():
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = b"audio output"
        mock_proc.stderr = b""
        mock_run.return_value = mock_proc

        run_ffmpeg(["-y", "-i", "input.wav", "output.mp3"])

        # Confere chamada do subprocess.run
        called_cmd = mock_run.call_args[0][0]
        assert "-protocol_whitelist" in called_cmd
        i_idx = called_cmd.index("-i")
        assert called_cmd[i_idx - 2:i_idx] == ["-protocol_whitelist", "file,pipe"]
        assert mock_run.call_args[1]["timeout"] == FFMPEG_TIMEOUT_SEC


def test_ffprobe_protocol_whitelist_and_timeout(tmp_path):
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "120.5\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        dummy = tmp_path / "test.mp3"
        duration = probe_duration(dummy)
        assert duration == 120.5

        called_cmd = mock_run.call_args[0][0]
        assert "-protocol_whitelist" in called_cmd
        p_idx = called_cmd.index("-protocol_whitelist")
        assert called_cmd[p_idx + 1] == "file"
        assert mock_run.call_args[1]["timeout"] == FFPROBE_TIMEOUT_SEC


def test_ffmpeg_timeout_raises_ffmpeg_error():
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 900)):
        with pytest.raises(FFmpegError, match="tempo limite"):
            run_ffmpeg(["-i", "test.wav"])


# --- Item 3: Middleware de cabeçalhos de segurança (CSP, X-Content-Type-Options, etc) ---

def test_security_headers_middleware():
    headers_dict = dict(SECURITY_HEADERS)
    assert b"content-security-policy" in headers_dict
    csp = headers_dict[b"content-security-policy"].decode("utf-8")
    assert "default-src 'self'" in csp
    assert "media-src 'self'" in csp
    assert "img-src 'self' data:" in csp
    assert "frame-ancestors 'none'" in csp

    assert headers_dict[b"x-content-type-options"] == b"nosniff"
    assert headers_dict[b"referrer-policy"] == b"no-referrer"


# --- Item 4: Fontes locais e remoção do Google Fonts ---

def test_index_html_has_no_google_fonts():
    index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in index_html
    assert "fonts.gstatic.com" not in index_html
    assert "/fonts.css" in index_html


def test_local_fonts_directory_has_woff2_files():
    fonts_dir = STATIC_DIR / "fonts"
    assert fonts_dir.is_dir()
    woff2_files = list(fonts_dir.glob("*.woff2"))
    assert len(woff2_files) >= 2, f"Esperado ao menos 2 arquivos .woff2, encontrado {len(woff2_files)}"

    fonts_css = (STATIC_DIR / "fonts.css").read_text(encoding="utf-8")
    assert "/fonts/" in fonts_css
    assert "fonts.gstatic.com" not in fonts_css
