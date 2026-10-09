"""
Speaker Memory Registry (Memória Dinâmica de Falantes).
Armazena a paleta de participantes identificados nos primeiros blocos
e injeta o contexto nos blocos paralelos subsequentes para eliminar rótulos genéricos.
"""

import re
from typing import Dict, List, Set, Optional, Any


class SpeakerMemoryRegistry:
    """Gerencia a memória global de falantes entre múltiplos blocos de áudio."""

    def __init__(self):
        # Mapeia {nome_padrao: descricao_ou_papel}
        self.speakers: Dict[str, str] = {}
        # Mapeia apelidos/variações para o nome canônico
        self.alias_map: Dict[str, str] = {}

    def add_speaker(self, name: str, description: str = ""):
        """Registra um novo falante na memória global."""
        clean_name = self.clean_speaker_name(name)
        if not clean_name or clean_name.lower().startswith(("falante", "speaker", "unknown", "voz")):
            return

        if clean_name not in self.speakers:
            self.speakers[clean_name] = description or "Participante identificado na gravação"
            self.alias_map[clean_name.lower()] = clean_name

    def extract_and_update_from_segments(self, segments: List[Dict[str, Any]]):
        """Extrai novos nomes de falantes a partir dos segmentos retornados."""
        for seg in segments:
            quemfala = seg.get("quemfala", "").strip()
            if quemfala:
                self.add_speaker(quemfala)

    def clean_speaker_name(self, name: str) -> str:
        """Limpa e padroniza o nome do falante."""
        name = re.sub(r"[\[\]]", "", name).strip()
        # Se for rótulo composto como "Réu / Bruno", mantém a padronização
        return name

    def get_prompt_context(self) -> str:
        """Gera o bloco de contexto de falantes para ser injetado no prompt da API."""
        if not self.speakers:
            return ""

        context = "\nPALETA DE FALANTES JÁ IDENTIFICADOS NESTA GRAVAÇÃO:\n"
        for name, desc in self.speakers.items():
            context += f"- [{name}]: {desc}\n"

        context += (
            "\nDIRETRIZES DE DIARIZAÇÃO:\n"
            "1. Utilize estritamente os nomes/papéis da paleta acima caso a voz corresponda a um deles.\n"
            "2. Evite rótulos genéricos como 'Falante 1' ou 'Falante 2'.\n"
            "3. Se uma NOVA pessoa inédita falar, identifique seu nome ou papel específico (ex: [Policial], [Testemunha], [Apresentador]).\n"
        )
        return context

    def canonicalize_name(self, name: str) -> str:
        """Mapeia variações de nome para o nome canônico da memória."""
        clean = self.clean_speaker_name(name)
        lower = clean.lower()

        # Busca direta no mapa de aliases
        if lower in self.alias_map:
            return self.alias_map[lower]

        # Busca parcial (ex: se o registro tem "Réu / Bruno" e veio "Bruno")
        for registered_lower, canonical in self.alias_map.items():
            if lower in registered_lower or registered_lower in lower:
                return canonical

        return clean
