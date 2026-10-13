import os
import sys
import io
import json
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional

# Force UTF-8 on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Garante inclusão de diretórios no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIARIZADOR_DIR = Path(__file__).resolve().parent

for p in [str(PROJECT_ROOT), str(DIARIZADOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from config_diarizador import (
    INPUT_DIR,
    PROCESSED_AUDIO_DIR,
    REPORTS_DIR,
    GEMINI_API_KEY,
    DEFAULT_MODEL
)
from audio_prep import FastAudioPreparer
from opus_encoder import OpusAudioPreparer
from silence_chunker import SilenceAwareChunker
from schema import FalaSegmento, TranscricaoChunkDiarizada
from vad_compact import VadAudioCompactor, map_compact_to_original


def format_seconds_to_timestamp(seconds: float) -> str:
    """Converte segundos float para formato HH:MM:SS ou MM:SS."""
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class HybridParallelDiarizer:
    """Orquestra o fatiamento em pausas, chamadas paralelas Pydantic e unificação temporal."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            self.client = None
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except Exception:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self.client = legacy_genai
            self.sdk_type = "google-generativeai"

    def transcribe_chunk_with_pydantic(
        self,
        chunk_meta: Dict[str, Any],
        speaker_context: str = "",
        max_retries: int = 4
    ) -> Dict[str, Any]:
        """
        Processa um bloco de áudio individual usando Structured Outputs Pydantic,
        com injeção de Speaker Memory Priming e retry automático.
        """
        chunk_path = Path(chunk_meta["chunk_path"])
        start_offset = chunk_meta["start_sec"]
        chunk_idx = chunk_meta["chunk_index"]

        prompt = (
            "Você é um especialista em transcrição e diarização de audiências judiciais, reuniões e telecomunicações. "
            "Transcreva com fidelidade absoluta o áudio em português, identificando cada interlocutor com seu nome ou papel real e indicando os tempos exatos.\n"
            f"{speaker_context}\n"
            "Diretrizes:\n"
            "1. 'quemfala': Identifique a pessoa (ex: 'Juiz', 'Réu / Bruno', 'Defensora', 'Guilherme', 'Bento'). Evite rótulos genéricos como 'Falante 1'.\n"
            "2. 'textodefala': Texto integral e correto do segmento.\n"
            "3. 'segundos_inicio' e 'segundos_fim': Segundos relativos ao início e fim da fala dentro deste trecho de áudio.\n"
            "4. 'timestamp': String no formato MM:SS - MM:SS relativo a este trecho."
        )

        # Determina o MIME type dinamicamente
        suffix = chunk_path.suffix.lower()
        if suffix in (".opus", ".ogg"):
            mime_type = "audio/ogg"
        elif suffix == ".wav":
            mime_type = "audio/wav"
        else:
            mime_type = "audio/mp3"

        with open(chunk_path, "rb") as f:
            audio_bytes = f.read()

        raw_text = "{}"
        prompt_tokens = 0
        candidate_tokens = 0
        total_tokens = 0
        api_latency = 0.0

        for attempt in range(1, max_retries + 1):
            try:
                t0 = time.time()
                if self.sdk_type == "google-genai":
                    from google.genai import types
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            prompt
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=TranscricaoChunkDiarizada,
                            max_output_tokens=8192,
                            temperature=0.1
                        )
                    )
                    api_latency = round(time.time() - t0, 3)
                    prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                    total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or (prompt_tokens + candidate_tokens)
                    raw_text = response.text.strip() if response.text else "{}"
                else:
                    model = self.client.GenerativeModel(
                        self.model_name,
                        generation_config={
                            "response_mime_type": "application/json",
                            "max_output_tokens": 8192,
                            "temperature": 0.1
                        }
                    )
                    response = model.generate_content([
                        {"mime_type": mime_type, "data": audio_bytes},
                        prompt
                    ])
                    api_latency = round(time.time() - t0, 3)
                    raw_text = response.text.strip() if hasattr(response, "text") and response.text else "{}"
                    prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                    total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

                break  # Sucesso! Sai do loop de retries
            except Exception as e:
                if attempt == max_retries:
                    print(f"\n❌ [Chunk {chunk_idx}] Erro definitivo após {max_retries} tentativas: {e}")
                    raw_text = "{}"
                else:
                    sleep_time = attempt * 3.5
                    print(f"\n⚠️ [Chunk {chunk_idx}] Rate limit/Erro temporário ({e}). Aguardando {sleep_time}s para retry...")
                    time.sleep(sleep_time)

        # Parse e validação estrita com Auto-Reparo de JSON resiliente
        segmentos_ajustados = []
        try:
            data = None
            try:
                data = json.loads(raw_text)
            except Exception:
                # Auto-Reparo: Se o JSON foi cortado antes de fechar chaves/aspas
                import re
                # Extrai todos os blocos {...} completos de segmentos
                matches = re.findall(r'\{[^{}]*"quemfala"[^{}]*"textodefala"[^{}]*\}', raw_text, re.DOTALL)
                if matches:
                    reconstructed = '{"segmentos": [' + ','.join(matches) + ']}'
                    try:
                        data = json.loads(reconstructed)
                    except Exception:
                        pass
                if not data:
                    # Tenta fechar a última chave
                    last_brace = raw_text.rfind("}")
                    if last_brace != -1:
                        data = json.loads(raw_text[:last_brace+1] + "]}")

            if data and isinstance(data, dict):
                parsed_chunk = TranscricaoChunkDiarizada.model_validate(data)

                # Ajuste de Offset Temporal pelo Processador Local (CPU)
                for seg in parsed_chunk.segmentos:
                    seg_abs_inicio = round(start_offset + seg.segundos_inicio, 2)
                    seg_abs_fim = round(start_offset + seg.segundos_fim, 2)
                    timestamp_global = f"{format_seconds_to_timestamp(seg_abs_inicio)} - {format_seconds_to_timestamp(seg_abs_fim)}"

                    segmentos_ajustados.append({
                        "quemfala": seg.quemfala,
                        "textodefala": seg.textodefala,
                        "timestamp": timestamp_global,
                        "segundos_inicio": seg_abs_inicio,
                        "segundos_fim": seg_abs_fim,
                        "chunk_origem": chunk_idx
                    })
        except Exception as err:
            print(f"\n[Aviso Chunk {chunk_idx}] Erro de parsing JSON após tentativa de reparo: {err}")

        return {
            "chunk_index": chunk_idx,
            "api_latency": api_latency,
            "prompt_tokens": prompt_tokens,
            "candidate_tokens": candidate_tokens,
            "total_tokens": total_tokens,
            "segmentos": segmentos_ajustados
        }

    def process_file(
        self,
        input_file: Path,
        target_chunk_sec: float = 90.0,
        max_parallel_workers: int = 8,
        codec: str = "opus",
        use_vad: bool = False
    ) -> Dict[str, Any]:
        """
        Executa o pipeline completo:
        1. Pré-processamento OPUS 16k VBR / MP3 64k Mono + Filtro Wideband (com VAD opcional)
        2. Fatiamento inteligente em silêncio (CPU)
        3. Transcrição e Diarização Paralela com Pydantic e Speaker Memory (Gemini)
        4. Costura temporal global determinística e Remapeamento VAD (CPU)
        5. Exportação em JSON, CSV e Markdown
        """
        input_file = Path(input_file)
        start_total = time.time()
        orig_dur = VadAudioCompactor.get_audio_duration(input_file)

        print(f"\n=================================================================")
        print(f"🚀 INICIANDO DIARIZADOR HÍBRIDO PARALELO COM PYDANTIC ({codec.upper()})")
        print(f"   Arquivo: {input_file.name}")
        print(f"   Duração Original: {round(orig_dur/60, 2)} min ({orig_dur:.1f}s)")
        print(f"   Tamanho Original: {round(input_file.stat().st_size / 1024, 2)} KB")
        print(f"   Codec de Áudio: {codec.upper()} ({'16 kbps VBR' if codec == 'opus' else '64 kbps CBR'})")
        print(f"   Modo VAD (Compactação): {'🟢 ATIVO (Remoção de silêncio + Correção de Timestamps)' if use_vad else '⚪ DESATIVADO (Áudio Contínuo)'}")
        print(f"   Target Chunk: {target_chunk_sec}s (Fatiamento em Pausas)")
        print(f"=================================================================")

        # 1. CPU: Preparar Áudio Otimizado (com ou sem VAD)
        ext = ".opus" if codec == "opus" else ".mp3"
        vad_tag = "_vad_compact" if use_vad else "_optimized"
        temp_audio = PROCESSED_AUDIO_DIR / f"{input_file.stem}{vad_tag}{ext}"

        segments_map = None
        silence_saved_sec = 0.0
        silence_saved_pct = 0.0
        comp_dur = orig_dur

        if use_vad:
            print(f"⚡ [CPU + VAD] Compactando áudio (removendo pausas mortas >0.4s)...", end=" ", flush=True)
            prep_meta = VadAudioCompactor.compact_and_encode_audio(
                input_path=input_file,
                output_path=temp_audio,
                codec=codec,
                bitrate="16k" if codec == "opus" else "64k",
                sample_rate=16000,
                channels=1,
                filter_wideband=True,
                noise_threshold_db=-35.0,
                min_silence_sec=0.4,
                pad_sec=0.10
            )
            segments_map = prep_meta["segments_map"]
            comp_dur = prep_meta["compact_duration_sec"]
            silence_saved_sec = prep_meta["silence_saved_sec"]
            silence_saved_pct = prep_meta["silence_saved_pct"]
            print(f"Concluído em {prep_meta['prep_time_sec']}s ({prep_meta['file_size_kb']} KB)")
            print(f"✂️ [VAD] Duração reduzida de {orig_dur:.1f}s para {comp_dur:.1f}s ({silence_saved_sec:.1f}s / {silence_saved_pct}% de economia de áudio/tokens!)")
        else:
            if codec == "opus":
                print(f"⚡ [CPU] Otimizando áudio (OPUS 16k VBR Mono + Filtro Wideband)...", end=" ", flush=True)
                prep_meta = OpusAudioPreparer.prepare_opus(
                    input_path=input_file,
                    output_path=temp_audio,
                    bitrate="16k",
                    sample_rate=16000,
                    channels=1,
                    filter_wideband=True
                )
            else:
                print(f"⚡ [CPU] Otimizando áudio (MP3 64k Mono + Filtro Wideband)...", end=" ", flush=True)
                prep_meta = FastAudioPreparer.prepare_mp3(
                    input_path=input_file,
                    output_path=temp_audio,
                    bitrate="64k",
                    sample_rate=16000,
                    channels=1,
                    filter_wideband=True
                )
            print(f"Concluído em {prep_meta['prep_time_sec']}s ({prep_meta['file_size_kb']} KB)")

        # 2. CPU: Fatiamento inteligente em momentos de silêncio
        chunks_dir = PROCESSED_AUDIO_DIR / f"{input_file.stem}_chunks_{codec}{'_vad' if use_vad else ''}"
        print(f"✂️ [CPU] Detectando pausas de silêncio e fatiando áudio...", end=" ", flush=True)
        chunks = SilenceAwareChunker.slice_audio(
            audio_path=temp_audio,
            output_dir=chunks_dir,
            target_chunk_sec=target_chunk_sec
        )
        print(f"Concluído! {len(chunks)} blocos criados.")
        for c in chunks:
            print(f"   -> Bloco {c['chunk_index']}: {format_seconds_to_timestamp(c['start_sec'])} até {format_seconds_to_timestamp(c['end_sec'])} ({c['duration_sec']}s)")

        # 3. NUVEM / GEMINI: Transcrição Paralela com Speaker Memory Priming
        from speaker_memory import SpeakerMemoryRegistry
        speaker_memory = SpeakerMemoryRegistry()

        t_cloud_start = time.time()
        chunk_results = []

        if chunks:
            # Passo 3.1: Bloco Âncora (Bloco 1) para descobrir os primeiros participantes
            print(f"\n🎙️ [Âncora] Processando Bloco 1 para descobrir a paleta inicial de falantes...", end=" ", flush=True)
            res_bloco_1 = self.transcribe_chunk_with_pydantic(chunks[0], speaker_context="")
            chunk_results.append(res_bloco_1)
            speaker_memory.extract_and_update_from_segments(res_bloco_1.get("segmentos", []))

            identified_spks = list(speaker_memory.speakers.keys())
            print(f"OK em {res_bloco_1['api_latency']}s | Falantes Detectados: {identified_spks or ['Em análise']}")

            # Passo 3.2: Blocos Restantes em Paralelo com Injeção de Memória
            if len(chunks) > 1:
                mem_context = speaker_memory.get_prompt_context()
                print(f"🌐 [Nuvem] Enviando {len(chunks)-1} blocos restantes em paralelo com Memória de Falantes...")

                with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
                    futures = [
                        executor.submit(self.transcribe_chunk_with_pydantic, chunk, mem_context)
                        for chunk in chunks[1:]
                    ]
                    for future in concurrent.futures.as_completed(futures):
                        res = future.result()
                        chunk_results.append(res)
                        # Atualiza dinamicamente se novos falantes forem identificados
                        speaker_memory.extract_and_update_from_segments(res.get("segmentos", []))
                        print(f"   ⚡ Bloco {res['chunk_index']}/{len(chunks)} finalizado em {res['api_latency']}s | Tokens: {res['total_tokens']}")

        cloud_duration = round(time.time() - t_cloud_start, 3)

        # Ordenar os resultados pela ordem cronológica dos blocos
        chunk_results.sort(key=lambda x: x["chunk_index"])

        # 4. CPU: Costura Global dos Segmentos, Remapeamento de Timestamps VAD e Padronização Canônica
        print(f"\n🧮 [CPU] Costurando linha do tempo, {'aplicando remapeamento de timestamps VAD e ' if use_vad else ''}padronizando falantes...")
        todos_segmentos = []
        total_prompt_tokens = 0
        total_candidate_tokens = 0
        total_tokens_geral = 0

        for cr in chunk_results:
            total_prompt_tokens += cr.get("prompt_tokens", 0)
            total_candidate_tokens += cr.get("candidate_tokens", 0)
            total_tokens_geral += cr["total_tokens"]

            for seg in cr.get("segmentos", []):
                # Normaliza o nome do falante para o nome canônico registrado na memória
                seg["quemfala"] = speaker_memory.canonicalize_name(seg["quemfala"])

                # Se o VAD foi aplicado, remapeia de volta para a linha do tempo original
                if use_vad and segments_map:
                    seg_c_inicio = seg["segundos_inicio"]
                    seg_c_fim = seg["segundos_fim"]

                    orig_inicio = map_compact_to_original(seg_c_inicio, segments_map)
                    orig_fim = map_compact_to_original(seg_c_fim, segments_map)
                    if orig_fim < orig_inicio:
                        orig_fim = orig_inicio

                    seg["segundos_inicio_compact"] = seg_c_inicio
                    seg["segundos_fim_compact"] = seg_c_fim
                    seg["segundos_inicio"] = orig_inicio
                    seg["segundos_fim"] = orig_fim
                    seg["timestamp"] = f"{format_seconds_to_timestamp(orig_inicio)} - {format_seconds_to_timestamp(orig_fim)}"

                todos_segmentos.extend([seg])

        total_elapsed = round(time.time() - start_total, 3)

        # Cálculo Financeiro (Gemini 2.5 Flash: $0.15 / 1M input, $0.60 / 1M output)
        cost_input_usd = (total_prompt_tokens / 1_000_000.0) * 0.15
        cost_output_usd = (total_candidate_tokens / 1_000_000.0) * 0.60
        cost_total_usd = round(cost_input_usd + cost_output_usd, 5)
        cost_total_brl = round(cost_total_usd * 5.70, 4)

        # 5. Exportar JSON Estruturado Final
        suffix_report = "_vad" if use_vad else ""
        output_json_path = REPORTS_DIR / f"{input_file.stem}_diarizacao_pydantic{suffix_report}.json"
        output_md_path = REPORTS_DIR / f"{input_file.stem}_diarizacao_pydantic{suffix_report}.md"

        final_payload = {
            "arquivo": input_file.name,
            "codec": codec,
            "vad_aplicado": use_vad,
            "duracao_original_segundos": round(orig_dur, 2),
            "duracao_compactada_segundos": round(comp_dur, 2),
            "economia_silencio_segundos": round(silence_saved_sec, 2),
            "economia_silencio_pct": round(silence_saved_pct, 2),
            "tempo_execucao_total_segundos": total_elapsed,
            "tempo_processamento_nuvem_segundos": cloud_duration,
            "metricas_tokens": {
                "prompt_tokens_audio": total_prompt_tokens,
                "candidate_tokens_texto": total_candidate_tokens,
                "total_tokens": total_tokens_geral
            },
            "custo_estimado": {
                "custo_usd": cost_total_usd,
                "custo_brl": cost_total_brl
            },
            "total_turnos_fala": len(todos_segmentos),
            "segmentos": todos_segmentos
        }

        if use_vad and segments_map:
            final_payload["vad_segments_map"] = segments_map

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, ensure_ascii=False, indent=2)

        # Exportar Markdown Formatado
        md_text = f"# Transcrição Diarizada com Timestamps e Pydantic{' (com VAD)' if use_vad else ''}\n\n"
        md_text += f"- **Arquivo:** `{input_file.name}`\n"
        md_text += f"- **Duração Original do Áudio:** `{round(orig_dur/60, 2)} min` ({round(orig_dur, 1)}s)\n"
        if use_vad:
            md_text += f"- **Duração Compactada (VAD):** `{round(comp_dur/60, 2)} min` ({round(comp_dur, 1)}s) — Economia de `{silence_saved_pct}%` ({round(silence_saved_sec, 1)}s)\n"
        md_text += f"- **Tempo Total de Execução:** `{total_elapsed}s` ({round(total_elapsed/60, 2)} min)\n"
        md_text += f"- **Tokens Utilizados:** `{total_tokens_geral:,}` (Entrada: `{total_prompt_tokens:,}`, Saída: `{total_candidate_tokens:,}`)\n"
        md_text += f"- **Custo Estimado:** `US$ {cost_total_usd}` (~ `R$ {cost_total_brl}`)\n"
        md_text += f"- **Total de Turnos de Fala:** `{len(todos_segmentos)}`\n\n"
        md_text += "---\n\n"

        for seg in todos_segmentos:
            md_text += f"**[{seg['timestamp']}] {seg['quemfala']}:**\n> {seg['textodefala']}\n\n"

        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        # 6. CPU: Gerar Alinhamento Palavra por Palavra
        from word_aligner import WordLevelTimestampAligner
        word_json_path = REPORTS_DIR / f"{input_file.stem}_palavra_por_palavra{suffix_report}.json"
        WordLevelTimestampAligner.process_diarization_json(
            json_input_path=output_json_path,
            json_output_path=word_json_path
        )

        print(f"\n=================================================================")
        print(f"✨ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print(f"   ⏱️ Tempo Total de Execução: {total_elapsed}s ({round(total_elapsed/60, 2)} min)")
        print(f"   📊 Total de Tokens: {total_tokens_geral:,} (Input: {total_prompt_tokens:,} | Output: {total_candidate_tokens:,})")
        print(f"   💰 Custo Estimado: US$ {cost_total_usd:.4f} (R$ {cost_total_brl:.3f})")
        if use_vad:
            print(f"   ✂️ Economia VAD: {silence_saved_pct}% ({silence_saved_sec:.1f}s silêncio cortado)")
        print(f"   📁 JSON Estruturado: {output_json_path}")
        print(f"   📁 JSON Palavra por Palavra: {word_json_path}")
        print(f"   📁 Markdown: {output_md_path}")
        print(f"=================================================================")

        return final_payload


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hybrid Parallel Diarizer CLI")
    parser.add_argument("--file", type=str, default=None, help="Arquivo de vídeo ou áudio para processar")
    parser.add_argument("--target-chunk", type=float, default=90.0, help="Tamanho alvo de cada fatia em segundos (padrão: 90s)")
    parser.add_argument("--workers", type=int, default=8, help="Número de threads simultâneas na API (padrão: 8)")
    parser.add_argument("--codec", type=str, choices=["opus", "mp3"], default="opus", help="Codec de áudio para compressão (padrão: opus)")
    parser.add_argument("--vad", action="store_true", help="Ativa compactação VAD com remapeamento de timestamps para o tempo original")

    args = parser.parse_args()

    diarizer = HybridParallelDiarizer()
    if args.file:
        target_path = Path(args.file)
    else:
        # Prioriza o videoplayback.mp4 se existir, ou o 999.mp4
        target_path = INPUT_DIR / "videoplayback.mp4"
        if not target_path.exists():
            target_path = INPUT_DIR / "999.mp4"

    if target_path.exists():
        diarizer.process_file(
            target_path,
            target_chunk_sec=args.target_chunk,
            max_parallel_workers=args.workers,
            codec=args.codec,
            use_vad=args.vad
        )
    else:
        print(f"Arquivo não encontrado: {target_path}")

