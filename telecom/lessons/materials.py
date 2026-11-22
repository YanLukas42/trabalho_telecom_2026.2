"""Material de aula a partir da aula diarizada: atividades individuais por aluno e plano da próxima aula.

A IA não ouve o áudio. Ela trabalha só com o texto da transcrição, então:
- um erro só entra se a citação existir literalmente nas falas daquele aluno;
- só os participantes marcados como aluno recebem folha de atividades;
- o professor confere o material antes de entregar: a transcrição automática também erra.
"""

import json
import logging
from dataclasses import dataclass
from typing import Protocol, Sequence

from pydantic import BaseModel, Field, ValidationError

from telecom.asr.gemini import GeminiClient
from telecom.diarization.models import SpeakerSegment
from telecom.metrics.text import normalize

logger = logging.getLogger(__name__)

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
MIN_EXERCISES = 3
MAX_EXERCISES = 10
DEFAULT_EXERCISES = 6
MAX_FOCUS_CHARS = 300
LESSON_TEMPERATURE = 0.4
LESSON_MAX_OUTPUT_TOKENS = 32_768
LESSON_MAX_RETRIES = 4


# ---------- Contrato de saída (chaves em inglês: contrato novo da interface web) ----------

class Mistake(BaseModel):
    quote: str = Field(description="Trecho exato que o aluno disse, copiado da transcrição")
    correction: str = Field(description="Forma correta em inglês")
    explanation: str = Field(description="Explicação curta em português, de uma frase")


class Exercise(BaseModel):
    kind: str = Field(description="'fill_blank', 'rewrite', 'multiple_choice' ou 'short_answer'")
    prompt: str = Field(description="Enunciado em inglês. Em fill_blank, marque a lacuna com ______")
    options: list[str] = Field(description="Alternativas; só em multiple_choice, senão lista vazia")
    answer: str = Field(description="Resposta esperada, para o gabarito do professor")


class StudentSheet(BaseModel):
    speaker: str = Field(description="Rótulo do aluno, igual ao informado na lista de participantes")
    strength: str = Field(description="Um ponto forte do aluno nesta aula, em português, de uma frase")
    mistakes: list[Mistake] = Field(description="Erros reais do aluno nesta aula; lista vazia se não houve")
    exercises: list[Exercise] = Field(description="Atividades que trabalham os erros desse aluno")


class PlanBlock(BaseModel):
    title: str = Field(description="Nome da etapa, em português")
    minutes: int = Field(description="Duração em minutos")
    description: str = Field(description="O que professor e alunos fazem nesta etapa, em português")


class LessonPlan(BaseModel):
    objective: str = Field(description="Objetivo da próxima aula, em português, de uma frase")
    topics: list[str] = Field(description="Tópicos de gramática e vocabulário a retomar, em português")
    blocks: list[PlanBlock] = Field(description="Etapas da aula, na ordem em que acontecem")
    homework: str = Field(description="Tarefa de casa sugerida, em português")


class LessonMaterials(BaseModel):
    students: list[StudentSheet] = Field(description="Uma folha por aluno informado")
    plan: LessonPlan = Field(description="Plano da próxima aula para a turma")


# ---------- Pedido ----------

@dataclass(frozen=True)
class Participant:
    label: str
    name: str
    role: str


@dataclass(frozen=True)
class LessonRequest:
    level: str
    participants: tuple[Participant, ...]
    exercises_per_student: int = DEFAULT_EXERCISES
    focus: str = ""

    def __post_init__(self) -> None:
        if self.level not in LEVELS:
            raise ValueError(f"Nível inválido: {self.level}. Use um destes: {', '.join(LEVELS)}")
        if not MIN_EXERCISES <= self.exercises_per_student <= MAX_EXERCISES:
            raise ValueError(f"Use de {MIN_EXERCISES} a {MAX_EXERCISES} atividades por aluno.")
        if len(self.focus) > MAX_FOCUS_CHARS:
            raise ValueError(f"O foco da aula aceita até {MAX_FOCUS_CHARS} caracteres.")
        for person in self.participants:
            if person.role not in (ROLE_TEACHER, ROLE_STUDENT):
                raise ValueError(f"Papel inválido para {person.name}: {person.role}")
        if not self.students:
            raise ValueError("Marque pelo menos um participante como aluno.")

    @property
    def students(self) -> tuple[Participant, ...]:
        return tuple(person for person in self.participants if person.role == ROLE_STUDENT)


# ---------- Prompt e validação (funções puras) ----------

_PROMPT_HEADER = (
    "Você é um coordenador pedagógico de inglês como língua estrangeira. Recebe a transcrição automática de uma aula "
    "(feita por reconhecimento de fala, sem o áudio) e prepara o material para o professor. "
    "Os alunos são brasileiros, nível {level} (CEFR).\n\n"
    "Participantes:\n{participants}\n\n"
    "Tarefas:\n"
    "1. Para cada ALUNO, em 'students': copie o rótulo em 'speaker'; aponte em 'mistakes' somente erros de inglês que "
    "esse aluno realmente cometeu, com 'quote' copiado literalmente da fala dele; escreva um ponto forte; e crie "
    "exatamente {count} atividades em 'exercises' que treinem esses erros, no nível {level}, com 'answer'. "
    "Varie os tipos de atividade. Use as frases e o vocabulário da própria aula. Se o aluno falou pouco, "
    "crie atividades sobre o tema da aula e deixe 'mistakes' vazio.\n"
    "2. Em 'plan', proponha a próxima aula para a turma: objetivo, tópicos a retomar, etapas com minutos "
    "(aquecimento, apresentação, prática, produção) e tarefa de casa.\n\n"
    "Regras:\n"
    "- Não invente erros. A transcrição pode ter errado uma palavra: ignore trechos que pareçam erro de "
    "reconhecimento e não de inglês.\n"
    "- Falas em português do aluno não são erro.\n"
    "- Não crie folha para o professor.\n"
    "{focus}\n"
    "Transcrição:\n"
)


def build_lesson_prompt(segments: Sequence[SpeakerSegment], request: LessonRequest) -> str:
    roles = {ROLE_TEACHER: "professor", ROLE_STUDENT: "aluno"}
    participants = "\n".join(f"- {p.label}: {p.name} ({roles[p.role]})" for p in request.participants)
    focus = f"- O professor quer foco em: {request.focus}\n" if request.focus.strip() else ""
    header = _PROMPT_HEADER.format(
        level=request.level, participants=participants, count=request.exercises_per_student, focus=focus
    )
    return header + "\n".join(f"[{i}] {s.speaker}: {s.text}" for i, s in enumerate(segments))


def parse_materials(raw_text: str) -> LessonMaterials:
    try:
        return LessonMaterials.model_validate(json.loads(raw_text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Material do Gemini inválido: {exc}") from exc


def validated_materials(
    materials: LessonMaterials, request: LessonRequest, segments: Sequence[SpeakerSegment]
) -> LessonMaterials:
    """Mantém só folhas de alunos do pedido e erros cuja citação existe nas falas do aluno."""
    spoken = {
        person.label: normalize(" ".join(s.text for s in segments if s.speaker == person.label))
        for person in request.students
    }
    sheets: list[StudentSheet] = []
    for sheet in materials.students:
        if sheet.speaker not in spoken:
            logger.info("Folha descartada (não é um aluno do pedido): %s", sheet.speaker)
            continue
        mistakes = []
        for mistake in sheet.mistakes:
            quote = normalize(mistake.quote)
            if quote and quote in spoken[sheet.speaker]:
                mistakes.append(mistake)
            else:
                logger.info("Erro descartado (citação ausente nas falas de %s): %s", sheet.speaker, mistake.quote)
        sheets.append(sheet.model_copy(update={
            "mistakes": mistakes,
            "exercises": sheet.exercises[: request.exercises_per_student],
        }))
    if not sheets:
        raise ValueError("A IA não devolveu atividades para nenhum aluno. Tente gerar de novo.")
    return LessonMaterials(students=sheets, plan=materials.plan)


class LessonWriter(Protocol):
    def write(self, segments: Sequence[SpeakerSegment], request: LessonRequest) -> LessonMaterials: ...


class GeminiLessonWriter:
    """Gera o material com o Gemini, só com texto. Não envia áudio."""

    def __init__(self, client: GeminiClient):
        self._client = client

    def write(self, segments: Sequence[SpeakerSegment], request: LessonRequest) -> LessonMaterials:
        result = self._client.generate_text(
            build_lesson_prompt(segments, request),
            response_schema=LessonMaterials,
            temperature=LESSON_TEMPERATURE,
            max_output_tokens=LESSON_MAX_OUTPUT_TOKENS,
            max_retries=LESSON_MAX_RETRIES,
        )
        logger.info("Material de aula: %d tokens", result.total_tokens)
        return validated_materials(parse_materials(result.text), request, segments)
