"""
Sample Audio Generator for Portuguese Speech Benchmark.
Generates reference WAV/MP3 speech samples using Windows SAPI TTS and registers Ground Truth.
"""

import json
import subprocess
from pathlib import Path

from config import SAMPLES_DIR, GROUND_TRUTH_FILE


SAMPLE_TEXTS = {
    "sample_telecom_01.wav": (
        "Este é um teste de transmissão para o projeto de telecomunicações. "
        "Estamos avaliando a fidelidade da transcrição de áudio em diferentes bitrates "
        "e taxas de compressão MP3 utilizando inteligência artificial."
    ),
    "sample_telecom_02_dialog.wav": (
        "Olá, você está ouvindo uma simulação de canal telefônico. "
        "Em redes celulares e VoIP, a otimização de largura de banda é crucial para garantir a qualidade de serviço "
        "e reduzir o consumo de dados dos usuários."
    )
}


def generate_tts_sample_windows(output_wav: Path, text: str):
    """Generates clean speech audio using Windows PowerShell SAPI SpeechSynthesizer."""
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    escaped_text = text.replace('"', '`"')
    ps_script = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.SetOutputToWaveFile('{str(output_wav)}')
    $synth.Speak('{escaped_text}')
    $synth.Dispose()
    """
    subprocess.run(["powershell", "-Command", ps_script], check=True)


def setup_default_dataset():
    """Generates default test samples and ground truth dataset."""
    ground_truth = {}

    for filename, text in SAMPLE_TEXTS.items():
        sample_path = SAMPLES_DIR / filename
        if not sample_path.exists():
            print(f"🎙️ Gerando áudio de teste: {filename}...")
            try:
                generate_tts_sample_windows(sample_path, text)
                print(f"   -> Salvo em: {sample_path}")
            except Exception as e:
                print(f"   -> Aviso: Não foi possível gerar TTS automático ({e}).")

        ground_truth[filename] = text

    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print(f"✅ Ground truth registrado em: {GROUND_TRUTH_FILE}")


if __name__ == "__main__":
    setup_default_dataset()
