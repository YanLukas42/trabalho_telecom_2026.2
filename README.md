# Trabalho Telecom 2026.2 — Áudio para Transcrição e Diarização com Gemini

Pesquisa em telecomunicações sobre como a compressão e o pré-processamento de áudio afetam a transcrição e a
separação de falantes pela API do Google Gemini, com foco em reduzir custo (tokens) e banda sem perder qualidade.

## Fases

- **Fase 1 — benchmark de MP3:** varredura de bitrate, taxa de amostragem, canal, filtros, VAD e ganho. Mede WER/CER,
  tokens, latência e custo. Ver [relatorio_avancos_fase1.md](relatorio_avancos_fase1.md).
- **Fase 2 — diarizador:** envia o áudio inteiro ao Gemini numa chamada e recebe o JSON no esquema padrão. Com VAD
  opcional, os tempos voltam para a linha do tempo original. O áudio enviado precisa caber em 20 MB (Opus 16 kbps cabe em ~2h50).

## Requisitos

- Python 3.10+
- FFmpeg e FFprobe no `PATH`
- Chave da API Gemini em `.env`:

```
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash   # opcional
```

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

Coloque as mídias em `input/`. Os resultados vão para `output/`.

```bash
# Diarização (usa videoplayback.mp4, 999.mp4 ou a primeira mídia de input/)
python -m telecom.cli.diarize
python -m telecom.cli.diarize --file input/aula.mp4 --codec opus --vad

# Benchmark: diarizacao (fase 2) ou mp3 (fase 1). --dry-run não chama a API.
python -m telecom.cli.benchmark diarizacao --dry-run
python -m telecom.cli.benchmark mp3 --file input/aula.mp4 --ground-truth referencia.json

# Testes (não chamam a API)
python -m pytest
```

## Saídas

| Pasta | Conteúdo |
|---|---|
| `output/diarizacao/reports/` | JSON, Markdown e alinhamento palavra a palavra por arquivo |
| `output/diarizacao/audio/` | Áudios intermediários (regeneráveis) |
| `output/benchmark/` | CSV, JSON e Markdown dos tratamentos da fase 1 |

## Arquitetura

Organização e padrões de código estão em [CLAUDE.md](CLAUDE.md).
