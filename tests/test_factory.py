import pytest

from telecom.diarization import factory


def test_gemini_needs_api_key(monkeypatch):
    monkeypatch.setattr(factory, "GEMINI_API_KEY", "")
    assert "GEMINI_API_KEY" in factory.engine_unavailable_reason("gemini")
    monkeypatch.setattr(factory, "GEMINI_API_KEY", "chave")
    assert factory.engine_unavailable_reason("gemini") is None


def test_pyannote_needs_token_and_local_deps(monkeypatch):
    monkeypatch.setattr(factory, "HF_TOKEN", "")
    assert "HF_TOKEN" in factory.engine_unavailable_reason("pyannote")
    monkeypatch.setattr(factory, "HF_TOKEN", "hf_x")
    monkeypatch.setattr(factory, "_installed", lambda module: False)
    assert "requirements-local.txt" in factory.engine_unavailable_reason("pyannote")


def test_unknown_engine_raises():
    with pytest.raises(ValueError):
        factory.engine_unavailable_reason("whatever")
    with pytest.raises(ValueError):
        factory.build_diarizer("whatever")
