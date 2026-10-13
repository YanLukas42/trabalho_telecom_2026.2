# 🎙️ Diarizador 2.0 — Separação de Falantes & Benchmark de MP3

Módulo de segunda fase focado especificamente na **Diarização (identificação e separação de múltiplos falantes)** em áudios e vídeos de audiências, reuniões e ligações.

## 🚀 Principais Recursos da Fase 2
1. **VAD Inteligente com Correção Temporal:** Remove silêncios mortos (>0.4s) economizando ~35% a 40% de tokens e banda, remapeando os timestamps do áudio compactado de volta para a linha do tempo original do vídeo (`map_compact_to_original`).
2. **Sem Normalização Pesada:** Processamento ultrarrápido em FFmpeg (< 0.5s por arquivo), eliminando o gargalo do `loudnorm`.
3. **Filtro de Voz Wideband (80 Hz a 7.500 Hz):** Preserva a frequência fundamental ($F_0$) e os formantes ($F_1$ a $F_4$) dos falantes, eliminando ruídos sem degradar o timbre da voz.
4. **Cálculo de Desvio WER vs. Baseline:** Mede o percentual exato de palavras alteradas em cada compressão (128k, 64k, 32k, 16k, 8k, VAD) em relação ao Baseline de 320k.
5. **Diarização Paralela Híbrida com Pydantic & Speaker Memory:** Fatiamento em silêncio com remapeamento temporal global.

## 💻 Como Executar
```bash
# Modo Dry-run do Benchmark (sem gastar API):
python diarizador2.0/run_diarizador.py --dry-run

# Modo Completo do Benchmark:
python diarizador2.0/run_diarizador.py

# Diarizador Híbrido Paralelo com VAD e Correção Temporal:
python diarizador2.0/hybrid_diarizer.py --file input/999.mp4 --codec opus --vad
```

