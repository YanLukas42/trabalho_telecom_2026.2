import json

import pytest

from telecom.diarization.models import SpeakerSegment
from telecom.lessons.materials import (
    GeminiLessonWriter,
    LessonMaterials,
    LessonRequest,
    Participant,
    build_lesson_prompt,
    parse_materials,
    validated_materials,
)

SEGMENTS = (
    SpeakerSegment("Professor", "What did you do yesterday?", 0, 4),
    SpeakerSegment("Aluno 1", "Yesterday I go to the market with my sister.", 4, 9),
    SpeakerSegment("Aluno 2", "I have twenty years old.", 9, 12),
)
PEOPLE = (
    Participant("Professor", "Rafael", "teacher"),
    Participant("Aluno 1", "Ana", "student"),
    Participant("Aluno 2", "Bia", "student"),
)


def request(**changes):
    return LessonRequest(**{"level": "A2", "participants": PEOPLE, **changes})


def exercise(prompt="Yesterday I ______ (go) to the market."):
    return {"kind": "fill_blank", "prompt": prompt, "options": [], "answer": "went"}


def sheet(speaker, mistakes, exercises=None):
    return {
        "speaker": speaker,
        "strength": "Fala com confiança.",
        "mistakes": mistakes,
        "exercises": exercises if exercises is not None else [exercise()],
    }


PLAN = {
    "objective": "Passado simples.",
    "topics": ["Past simple"],
    "blocks": [{"title": "Aquecimento", "minutes": 10, "description": "Conversa."}],
    "homework": "Escrever 5 frases.",
}


def materials(*sheets) -> LessonMaterials:
    return LessonMaterials.model_validate({"students": list(sheets), "plan": PLAN})


def test_request_needs_a_student_and_a_valid_level():
    with pytest.raises(ValueError, match="aluno"):
        request(participants=(PEOPLE[0],))
    with pytest.raises(ValueError, match="Nível"):
        request(level="D9")
    with pytest.raises(ValueError, match="atividades"):
        request(exercises_per_student=1)
    with pytest.raises(ValueError, match="Papel"):
        request(participants=(Participant("Professor", "Rafael", "diretor"),))


def test_prompt_lists_participants_and_transcript_but_no_sheet_for_teacher():
    prompt = build_lesson_prompt(SEGMENTS, request(focus="past simple"))
    assert "- Aluno 1: Ana (aluno)" in prompt
    assert "- Professor: Rafael (professor)" in prompt
    assert "[1] Aluno 1: Yesterday I go to the market" in prompt
    assert "past simple" in prompt
    assert "exatamente 6 atividades" in prompt


def test_keeps_only_mistakes_quoted_from_that_student():
    raw = materials(
        sheet("Aluno 1", [
            {"quote": "Yesterday I go to the market", "correction": "Yesterday I went", "explanation": "Passado."},
            {"quote": "I have twenty years old", "correction": "I am twenty", "explanation": "Idade com be."},
            {"quote": "never said this", "correction": "x", "explanation": "x"},
        ]),
    )
    result = validated_materials(raw, request(), SEGMENTS)
    quotes = [m.quote for m in result.students[0].mistakes]
    # "I have twenty years old" é do Aluno 2, e a terceira citação não existe: só a primeira fica.
    assert quotes == ["Yesterday I go to the market"]


def test_quote_match_ignores_case_and_punctuation():
    raw = materials(sheet("Aluno 2", [{"quote": "i have twenty years old!", "correction": "I am twenty", "explanation": "x"}]))
    assert len(validated_materials(raw, request(), SEGMENTS).students[0].mistakes) == 1


def test_drops_sheets_for_the_teacher_and_unknown_speakers():
    raw = materials(sheet("Professor", []), sheet("Fantasma", []), sheet("Aluno 1", []))
    result = validated_materials(raw, request(), SEGMENTS)
    assert [s.speaker for s in result.students] == ["Aluno 1"]


def test_trims_extra_exercises():
    raw = materials(sheet("Aluno 1", [], [exercise(f"Q{i}") for i in range(8)]))
    result = validated_materials(raw, request(exercises_per_student=3), SEGMENTS)
    assert len(result.students[0].exercises) == 3


def test_fails_when_no_student_sheet_survives():
    with pytest.raises(ValueError, match="nenhum aluno"):
        validated_materials(materials(sheet("Professor", [])), request(), SEGMENTS)


def test_parse_rejects_invalid_json_and_wrong_schema():
    with pytest.raises(ValueError, match="inválido"):
        parse_materials("not json")
    with pytest.raises(ValueError, match="inválido"):
        parse_materials(json.dumps({"students": []}))


def test_gemini_writer_uses_text_only_and_validates():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate_text(self, prompt, **options):
            self.calls.append((prompt, options))
            text = materials(sheet("Aluno 1", [])).model_dump_json()
            return type("Result", (), {"text": text, "total_tokens": 10})()

    client = FakeClient()
    result = GeminiLessonWriter(client).write(SEGMENTS, request())
    assert result.students[0].speaker == "Aluno 1"
    assert client.calls[0][1]["response_schema"] is LessonMaterials
