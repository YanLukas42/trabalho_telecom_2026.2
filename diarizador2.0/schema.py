"""
Pydantic Schemas para Estruturação Estrita de Diarização.
Garante que o Gemini retorne exatamente o JSON esperado sem alucinações de formato.
"""

from typing import List
from pydantic import BaseModel, Field


class FalaSegmento(BaseModel):
    quemfala: str = Field(
        description="Identificação do falante (ex: Juiz, Réu / Bruno, Defensora, Promotor, Falante 1, etc.)"
    )
    textodefala: str = Field(
        description="Transcrição exata e fiel do que foi dito neste trecho de fala"
    )
    timestamp: str = Field(
        description="Intervalo de tempo no formato MM:SS - MM:SS (ex: '00:05 - 00:18')"
    )
    segundos_inicio: float = Field(
        description="Segundo exato de início da fala no trecho de áudio (ex: 5.2)"
    )
    segundos_fim: float = Field(
        description="Segundo exato de término da fala no trecho de áudio (ex: 18.4)"
    )


class TranscricaoChunkDiarizada(BaseModel):
    segmentos: List[FalaSegmento] = Field(
        description="Lista ordenada cronologicamente com todas as falas e seus respectivos interlocutores"
    )


class PalavraTimestamp(BaseModel):
    palavra: str = Field(description="Palavra individual falada")
    quemfala: str = Field(description="Identificação de quem falou esta palavra")
    segundos_inicio: float = Field(description="Segundo exato de início da palavra no áudio")
    segundos_fim: float = Field(description="Segundo exato de término da palavra no áudio")
    timestamp: str = Field(description="Timestamp formatado MM:SS.mmm - MM:SS.mmm")
    chunk_origem: int = Field(default=1, description="Bloco de áudio de origem")


class TranscricaoWordLevel(BaseModel):
    arquivo: str
    total_palavras: int
    palavras: List[PalavraTimestamp]
