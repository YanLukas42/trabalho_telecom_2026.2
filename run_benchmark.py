"""
Main CLI Entry Point for MP3-Gemini AI Benchmark.
Usage:
    python run_benchmark.py --dry-run
    python run_benchmark.py --sample dataset/samples/sample_telecom_01.wav
    python run_benchmark.py --generate-samples
"""

import argparse
import sys
import io
from pathlib import Path

# Force UTF-8 encoding on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import INPUT_DIR, SAMPLES_DIR, GROUND_TRUTH_FILE
from dataset.create_sample import setup_default_dataset
from src.pipeline.runner import BenchmarkRunner
from src.pipeline.report import ReportGenerator
from src.visualizer.plots import BenchmarkVisualizer


def main():
    parser = argparse.ArgumentParser(
        description="MP3-Gemini AI Optimizer: Scientific Audio Compression Benchmark for ASR"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa apenas as conversões de áudio MP3 localmente sem chamar a API do Gemini"
    )
    parser.add_argument(
        "--sample",
        type=str,
        default=None,
        help="Caminho para um arquivo de áudio ou vídeo específico (.mp4, .wav, .mp3, etc.)"
    )
    parser.add_argument(
        "--generate-samples",
        action="store_true",
        help="Gera áudios de teste e arquivo ground_truth.json"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Modelo Gemini a ser utilizado (ex: gemini-2.5-flash, gemini-2.0-flash)"
    )

    args = parser.parse_args()

    # Supported media extensions
    valid_extensions = {".mp4", ".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".mkv", ".webm"}

    # Determine audio/video files to process
    if args.sample:
        audio_files = [Path(args.sample)]
    else:
        # Check input folder first, then dataset/samples
        audio_files = [
            f for f in INPUT_DIR.glob("*.*")
            if f.suffix.lower() in valid_extensions and not f.name.startswith(".")
        ]
        if not audio_files:
            audio_files = [
                f for f in SAMPLES_DIR.glob("*.*")
                if f.suffix.lower() in valid_extensions and not f.name.startswith(".")
            ]

    # If still empty and generate-samples was passed or no files exist
    if not audio_files:
        if args.generate_samples:
            print("\n📦 Preparando dataset inicial de áudios...")
            setup_default_dataset()
            audio_files = [
                f for f in SAMPLES_DIR.glob("*.*")
                if f.suffix.lower() in valid_extensions and not f.name.startswith(".")
            ]
        else:
            print("\n❌ Nenhum arquivo de áudio ou vídeo encontrado em 'input/' ou 'dataset/samples/'!")
            print("   Coloque seus arquivos (.mp4, .mp3, .wav) na pasta 'input/' ou execute com --generate-samples.")
            sys.exit(1)

    print(f"\n=================================================================")
    print(f"🚀 INICIANDO BENCHMARK: MP3 vs. GOOGLE GEMINI API")
    print(f"   Modo: {'🔍 DRY-RUN (Offline / Sem gastos de API)' if args.dry_run else '🌐 COMPLETO (Com API Gemini)'}")
    print(f"   Modelo IA: {args.model}")
    print(f"   Arquivos de Teste: {len(audio_files)}")
    print(f"=================================================================")

    runner = BenchmarkRunner(model_name=args.model)
    all_results = []

    for audio_file in audio_files:
        if audio_file.name.endswith(".gitkeep"):
            continue
        file_results = runner.run_experiment_on_file(audio_file, dry_run=args.dry_run)
        all_results.extend(file_results)

    if not all_results:
        print("\n⚠️ Nenhum resultado coletado.")
        return

    # Export Reports
    print("\n📊 Gerando Relatórios e Métricas...")
    reports = ReportGenerator.export_all(all_results)
    for fmt, p in reports.items():
        print(f"   -> Relatório {fmt.upper()}: {p}")

    # Generate Visual Plots
    print("\n📈 Gerando Gráficos Comparativos...")
    viz = BenchmarkVisualizer()
    plots = viz.plot_all(all_results)
    for p in plots:
        print(f"   -> Gráfico salvo: {p.name}")

    print("\n✨ Benchmark concluído com sucesso!")
    print(f"📁 Confira os resultados completos na pasta: output/")


if __name__ == "__main__":
    main()
