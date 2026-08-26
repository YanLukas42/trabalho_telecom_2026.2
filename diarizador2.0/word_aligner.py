"""
Algoritmo de Alinhamento Palavra por Palavra (Word-Level Timestamp Aligner).
Processa o JSON de diarização e distribui timestamps individuais para cada palavra
utilizando ponderação fonética, contagem silábica e pausas de pontuação.
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Force UTF-8 on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIARIZADOR_DIR = Path(__file__).resolve().parent

for p in [str(PROJECT_ROOT), str(DIARIZADOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from config_diarizador import REPORTS_DIR
from schema import PalavraTimestamp, TranscricaoWordLevel


def format_ms_timestamp(seconds: float) -> str:
    """Formata segundos em MM:SS.mmm."""
    seconds = max(0.0, seconds)
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{mins:02d}:{secs:02d}.{millis:03d}"


class WordLevelTimestampAligner:
    """Regulador e distribuidor de timestamps palavra por palavra."""

    VOWELS = set("aeiouáéíóúâêîôûãõàü")

    @classmethod
    def estimate_phonetic_weight(cls, word: str) -> float:
        """
        Calcula o peso fonético de uma palavra:
        - Tamanho de caracteres limpos
        - Quantidade de núcleos vocálicos (sílabas aproximadas)
        - Pausas adicionais por pontuação (vírgula, ponto, interrogação)
        """
        clean_word = re.sub(r"[^\w]", "", word.lower())
        if not clean_word:
            return 1.0

        # Contagem de vogais
        vowel_count = sum(1 for char in clean_word if char in cls.VOWELS)
        base_weight = max(1.0, len(clean_word) * 0.7 + vowel_count * 0.8)

        # Se a palavra original termina com pontuação, ganha um peso extra de pausa
        if word.endswith((".", "?", "!")):
            base_weight += 1.8
        elif word.endswith((",", ";", ":", "...")):
            base_weight += 1.0

        return base_weight

    @classmethod
    def align_segment_to_words(cls, segment: Dict[str, Any]) -> List[PalavraTimestamp]:
        """
        Divide o texto de um segmento em palavras individuais e calcula
        os timestamps exatos de início e fim para cada uma.
        """
        raw_text = segment.get("textodefala", "").strip()
        quemfala = segment.get("quemfala", "Falante")
        t_inicio = segment.get("segundos_inicio", 0.0)
        t_fim = segment.get("segundos_fim", 0.0)
        chunk_origem = segment.get("chunk_origem", 1)

        duracao_total = max(0.2, t_fim - t_inicio)
        raw_words = raw_text.split()

        if not raw_words:
            return []

        # Calcula o peso fonético de cada palavra
        weights = [cls.estimate_phonetic_weight(w) for w in raw_words]
        total_weight = sum(weights)

        words_output = []
        current_time = t_inicio

        for i, word in enumerate(raw_words):
            # Proporção da duração deste segmento para esta palavra
            word_duration = (weights[i] / total_weight) * duracao_total
            w_inicio = round(current_time, 3)
            w_fim = round(current_time + word_duration, 3)

            # Garante que a última palavra feche exatamente no fim do segmento
            if i == len(raw_words) - 1:
                w_fim = round(t_fim, 3)

            timestamp_str = f"{format_ms_timestamp(w_inicio)} - {format_ms_timestamp(w_fim)}"

            item = PalavraTimestamp(
                palavra=word,
                quemfala=quemfala,
                segundos_inicio=w_inicio,
                segundos_fim=w_fim,
                timestamp=timestamp_str,
                chunk_origem=chunk_origem
            )
            words_output.append(item)
            current_time = w_fim

        return words_output

    @classmethod
    def process_diarization_json(
        cls,
        json_input_path: Path,
        json_output_path: Optional[Path] = None
    ) -> TranscricaoWordLevel:
        """
        Lê o JSON de diarização por segmentos gerado pelo Pydantic
        e gera o JSON completo palavra por palavra.
        """
        json_input_path = Path(json_input_path)
        if not json_input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {json_input_path}")

        with open(json_input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        arquivo_nome = data.get("arquivo", json_input_path.stem)
        segmentos = data.get("segmentos", [])

        todas_palavras = []
        for seg in segmentos:
            palavras_seg = cls.align_segment_to_words(seg)
            todas_palavras.extend(palavras_seg)

        resultado = TranscricaoWordLevel(
            arquivo=arquivo_nome,
            total_palavras=len(todas_palavras),
            palavras=todas_palavras
        )

        if not json_output_path:
            json_output_path = REPORTS_DIR / f"{json_input_path.stem.replace('_diarizacao_pydantic', '')}_palavra_por_palavra.json"

        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(resultado.model_dump(), f, ensure_ascii=False, indent=2)

        print(f"\n=======================================================")
        print(f"✨ ALINHAMENTO PALAVRA POR PALAVRA CONCLUÍDO!")
        print(f"   Arquivo Original: {arquivo_nome}")
        print(f"   Total de Palavras Alinhadas: {len(todas_palavras)}")
        print(f"   Salvo em: {json_output_path}")
        print(f"=======================================================")

        return resultado


if __name__ == "__main__":
    target_json = REPORTS_DIR / "999_diarizacao_pydantic.json"
    if target_json.exists():
        WordLevelTimestampAligner.process_diarization_json(target_json)
