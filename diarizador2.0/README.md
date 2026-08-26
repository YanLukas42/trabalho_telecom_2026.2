# 🎙️ Diarizador 2.0 — Separação de Falantes & Benchmark de MP3

Módulo de segunda fase focado especificamente na **Diarização (identificação e separação de múltiplos falantes)** em áudios e vídeos de audiências, reuniões e ligações.

## 🚀 Principais Ajustes da Fase 2
1. **Sem VAD (Áudio Contínuo):** O áudio é mantido sem cortes temporais para preservar a prosódia, pausas naturais e sincronia temporal dos falantes.
2. **Sem Normalização Pesada:** Processamento ultrarrápido em FFmpeg (< 0.5s por arquivo), eliminando o gargalo de 19s do `loudnorm`.
3. **Filtro de Voz Wideband (80 Hz a 7.500 Hz):** Preserva a frequência fundamental ($F_0$) e os formantes ($F_1$ a $F_4$) dos falantes, eliminando ruídos sem degradar o timbre da voz.
4. **Cálculo de Desvio WER vs. Baseline:** Mede o percentual exato de palavras alteradas em cada compressão (128k, 64k, 32k, 16k, 8k) em relação ao Baseline de 320k de máxima qualidade.

## 💻 Como Executar
```bash
# Modo Dry-run (sem gastar API):
python diarizador2.0/run_diarizador.py --dry-run

# Modo Completo com Diarização do Gemini:
python diarizador2.0/run_diarizador.py
```
