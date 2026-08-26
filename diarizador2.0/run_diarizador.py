"""
Runner CLI para o Diarizador 2.0.
Executa a matriz otimizada de diarização (sem VAD, sem loudnorm, filtro wideband)
e calcula o desvio (WER) relativo ao Baseline de 320k.
"""

import sys
import argparse
import json
import pandas as pd
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Adiciona o diretório raiz ao sys.path para importar pacotes
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIARIZADOR_DIR = Path(__file__).resolve().parent

for p in [str(PROJECT_ROOT), str(DIARIZADOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from config_diarizador import (
    INPUT_DIR,
    PROCESSED_AUDIO_DIR,
    REPORTS_DIR,
    DIARIZATION_EXPERIMENT_MATRIX,
    DEFAULT_MODEL
)
from audio_prep import FastAudioPreparer
from gemini_diarizer import GeminiDiarizer
from evaluator import DiarizationEvaluator


def run_diarization_suite(audio_file: Path, dry_run: bool = False, model_name: str = DEFAULT_MODEL):
    audio_file = Path(audio_file)
    print(f"\n=================================================================")
    print(f"🎙️ DIARIZADOR 2.0: BENCHMARK DE SEPARAÇÃO DE FALANTES")
    print(f"   Arquivo: {audio_file.name}")
    print(f"   Modo: {'🔍 DRY-RUN (Offline)' if dry_run else '🌐 API GEMINI (Diarização Ativa)'}")
    print(f"   Modelo: {model_name}")
    print(f"   Ajustes: Sem VAD (Áudio Contínuo) | Sem Loudnorm Pesado | Filtro Wideband")
    print(f"=================================================================")

    original_size = audio_file.stat().st_size
    diarizer = GeminiDiarizer(model_name=model_name)
    results = []
    baseline_transcript = ""

    # 1. Processar e transcrever todos os tratamentos
    for t in DIARIZATION_EXPERIMENT_MATRIX:
        t_id = t["id"]
        t_label = t["label"]
        output_name = f"{audio_file.stem}_{t_id}.mp3"
        output_mp3 = PROCESSED_AUDIO_DIR / output_name

        print(f"\n⚡ Processando: {t_label}...", end=" ", flush=True)

        meta = FastAudioPreparer.prepare_mp3(
            input_path=audio_file,
            output_path=output_mp3,
            bitrate=t["bitrate"],
            sample_rate=t["sample_rate"],
            channels=t["channels"],
            filter_wideband=t["filter_wideband"]
        )

        size_kb = meta["file_size_kb"]
        saved_pct = round(((original_size - meta["file_size_bytes"]) / original_size) * 100.0, 2)

        transcript = ""
        tokens = 0
        api_lat = 0.0

        if not dry_run:
            try:
                res = diarizer.diarize(output_mp3)
                transcript = res["diarized_transcript"]
                tokens = res["total_tokens"]
                api_lat = res["api_latency_sec"]
                speaker_turns = DiarizationEvaluator.count_speaker_turns(transcript)

                if t.get("is_baseline"):
                    baseline_transcript = transcript

                print(f"OK | Tokens: {tokens} | Turnos: {speaker_turns} | API: {api_lat}s")
            except Exception as e:
                print(f"ERRO: {e}")
                transcript = f"[ERRO: {e}]"
        else:
            print(f"OK (Dry-Run: {size_kb} KB em {meta['prep_time_sec']}s)")

        results.append({
            "treatment_id": t_id,
            "treatment_label": t_label,
            "bitrate": t["bitrate"],
            "sample_rate": t["sample_rate"],
            "channels": t["channels"],
            "filter_wideband": t["filter_wideband"],
            "file_size_kb": size_kb,
            "bandwidth_saved_pct": saved_pct,
            "prep_time_sec": meta["prep_time_sec"],
            "api_latency_sec": api_lat,
            "total_tokens": tokens,
            "transcript": transcript,
            "speaker_turns": DiarizationEvaluator.count_speaker_turns(transcript) if transcript else 0
        })

    # 2. Calcular WER relativo contra o Baseline 320k
    if not dry_run and baseline_transcript:
        for r in results:
            wer = DiarizationEvaluator.calculate_wer(baseline_transcript, r["transcript"])
            r["wer_vs_baseline_320k"] = wer
    else:
        for r in results:
            r["wer_vs_baseline_320k"] = 0.0

    # 3. Exportar Relatório
    df = pd.DataFrame(results)
    csv_path = REPORTS_DIR / f"{audio_file.stem}_diarizacao_results.csv"
    md_path = REPORTS_DIR / f"{audio_file.stem}_diarizacao_results.md"

    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Gerar Markdown Tabular
    summary_cols = ["treatment_label", "file_size_kb", "bandwidth_saved_pct", "wer_vs_baseline_320k", "speaker_turns", "total_tokens", "api_latency_sec"]
    summary_df = df[[c for c in summary_cols if c in df.columns]]

    md_text = f"# Relatório Diarizador 2.0: Separação de Falantes e Otimização MP3\n\n"
    md_text += f"Arquivo de Entrada: `{audio_file.name}` (Tamanho: {round(original_size/1024, 2)} KB)\n\n"
    md_text += summary_df.to_markdown(index=False)
    md_text += "\n\n## Transcrições Diarizadas por Tratamento\n\n"

    for r in results:
        md_text += f"### {r['treatment_label']}\n"
        md_text += f"- **Tamanho:** `{r['file_size_kb']} KB` ({r['bandwidth_saved_pct']}% salvo)\n"
        md_text += f"- **Desvio WER vs Baseline 320k:** `{r.get('wer_vs_baseline_320k', 0.0)}%` | **Turnos de Fala:** `{r['speaker_turns']}`\n"
        md_text += f"- **Transcrição Diarizada:**\n\n```text\n{r['transcript']}\n```\n\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"\n📊 Relatórios Gerados:")
    print(f"   -> CSV: {csv_path}")
    print(f"   -> Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Diarizador 2.0 CLI")
    parser.add_argument("--dry-run", action="store_true", help="Executa apenas a preparação de áudio")
    parser.add_argument("--sample", type=str, default=None, help="Caminho do áudio/vídeo")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Modelo Gemini")

    args = parser.parse_args()

    if args.sample:
        files = [Path(args.sample)]
    else:
        files = list(INPUT_DIR.glob("*.mp4")) + list(INPUT_DIR.glob("*.mp3")) + list(INPUT_DIR.glob("*.wav"))

    if not files:
        print("❌ Nenhum arquivo encontrado na pasta input/!")
        sys.exit(1)

    for f in files:
        run_diarization_suite(f, dry_run=args.dry_run, model_name=args.model)


if __name__ == "__main__":
    main()
