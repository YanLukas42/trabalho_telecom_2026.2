import json

import pytest

from telecom.diarization.models import SpeakerSegment
from telecom.diarization.review import (
    FalanteIdentificado,
    GeminiReviewer,
    RevisaoFala,
    RevisaoTranscricao,
    apply_review,
    build_review_prompt,
    identified_names,
    parse_review,
    valid_reviews,
)
from telecom.asr.gemini import GenerationResult

SEGMENTS = (
    SpeakerSegment("SPEAKER_00", "Bom dia, doutor Carlos. Pode começar.", 0.0, 3.0),
    SpeakerSegment("SPEAKER_01", "Obrigado, a senhora fica à vontade.", 3.5, 6.0),
)


def _review(falantes=(), revisoes=()):
    return RevisaoTranscricao(falantes=list(falantes), revisoes=list(revisoes))


def test_name_with_literal_evidence_and_high_confidence_is_applied():
    review = _review([FalanteIdentificado(rotulo="SPEAKER_00", nome="Dr. Carlos", confianca=0.9,
                                          evidencia="doutor Carlos")])
    assert identified_names(review, SEGMENTS) == {"SPEAKER_00": "Dr. Carlos"}


def test_name_without_evidence_in_text_is_rejected():
    review = _review([FalanteIdentificado(rotulo="SPEAKER_01", nome="Maria", confianca=0.95,
                                          evidencia="meu nome é Maria")])
    assert identified_names(review, SEGMENTS) == {}


def test_low_confidence_is_rejected():
    review = _review([FalanteIdentificado(rotulo="SPEAKER_00", nome="Carlos", confianca=0.4,
                                          evidencia="doutor Carlos")])
    assert identified_names(review, SEGMENTS) == {}


def test_empty_name_or_evidence_is_rejected():
    review = _review([
        FalanteIdentificado(rotulo="SPEAKER_00", nome="", confianca=1.0, evidencia="doutor Carlos"),
        FalanteIdentificado(rotulo="SPEAKER_01", nome="Ana", confianca=1.0, evidencia=""),
    ])
    assert identified_names(review, SEGMENTS) == {}


def test_review_must_quote_text_from_the_indicated_utterance():
    ok = RevisaoFala(indice_fala=0, tipo="nome", trecho="doutor Carlos", sugestao="Dr. Carlos", motivo="grafia")
    wrong_utterance = RevisaoFala(indice_fala=1, tipo="nome", trecho="doutor Carlos", sugestao="x", motivo="y")
    out_of_range = RevisaoFala(indice_fala=9, tipo="legenda", trecho="x", sugestao="y", motivo="z")
    kept = valid_reviews(_review(revisoes=[ok, wrong_utterance, out_of_range]), SEGMENTS)
    assert kept == [ok]


def test_apply_review_keeps_original_text_untouched():
    review = _review([FalanteIdentificado(rotulo="SPEAKER_00", nome="Dr. Carlos", confianca=0.9,
                                          evidencia="doutor Carlos")])
    applied = apply_review(review, SEGMENTS)
    assert applied.names == {"SPEAKER_00": "Dr. Carlos"}
    assert SEGMENTS[0].text == "Bom dia, doutor Carlos. Pode começar."


def test_prompt_contains_numbered_text_and_no_audio_instruction():
    prompt = build_review_prompt(SEGMENTS)
    assert "[0] SPEAKER_00: Bom dia, doutor Carlos." in prompt
    assert "NÃO ouve o áudio" in prompt


def test_invalid_review_json_raises():
    with pytest.raises(ValueError, match="Revisão do Gemini inválida"):
        parse_review("não é json")


class StubTextClient:
    def __init__(self, text):
        self.text = text
        self.kwargs = None

    def generate_text(self, prompt, **kwargs):
        self.kwargs = kwargs
        return GenerationResult(self.text, 1, 1, 2, 0.1)


def test_gemini_reviewer_sends_text_only_and_parses_answer():
    payload = {"falantes": [{"rotulo": "SPEAKER_00", "nome": "Dr. Carlos", "confianca": 0.9,
                             "evidencia": "doutor Carlos"}],
               "revisoes": []}
    client = StubTextClient(json.dumps(payload))
    review = GeminiReviewer(client).review(SEGMENTS)
    assert review.falantes[0].nome == "Dr. Carlos"
    assert client.kwargs["response_schema"] is RevisaoTranscricao
