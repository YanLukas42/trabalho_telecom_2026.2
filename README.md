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
HF_TOKEN=hf_...                       # só para o pyannote (modelo restrito)
```
- Para a diarização local (pyannote + whisper): `pip install -r requirements-local.txt`. Aceite os termos dos modelos
  `pyannote/speaker-diarization-3.1` e `pyannote/segmentation-3.0` no Hugging Face antes.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

Coloque as mídias em `input/`. Os resultados vão para `output/`.

```bash
# Interface web para professores (Pauta): veja a seção "Interface web" abaixo
python -m telecom.cli.serve

# Diarização via CLI (usa videoplayback.mp4, 999.mp4 ou a primeira mídia de input/)
python -m telecom.cli.diarize
python -m telecom.cli.diarize --file input/aula.mp4 --codec opus --vad

# Benchmark: diarizacao (fase 2) ou mp3 (fase 1). --dry-run não chama a API.
python -m telecom.cli.benchmark diarizacao --dry-run
python -m telecom.cli.benchmark mp3 --file input/aula.mp4 --ground-truth referencia.json

# Testes (não chamam a API)
python -m pytest
```

## Interface web (MVP: Pauta)

```bash
python -m telecom.cli.serve            # http://127.0.0.1:8000
```

Pensada para professores de inglês. Fluxo:

1. **Aula:** envie a gravação (áudio ou vídeo). A transcrição separa quem falou e o tempo de cada fala.
   Confirme quem é o professor e corrija os nomes: só os alunos recebem folha.
2. **Atividades:** escolha o nível (CEFR), o número de atividades e, se quiser, o foco. A IA cria, para cada aluno,
   os erros reais da aula (marcados a caneta vermelha na transcrição) e atividades com gabarito.
3. **Próxima aula:** plano com objetivo, tópicos, etapas com minutos e tarefa de casa.
4. **PDF:** "Imprimir" abre a janela de impressão do navegador; escolha "Salvar como PDF". Há folha por aluno,
   todas as folhas, gabarito e plano.

A IA lê só o texto da transcrição, sem ouvir o áudio: confira o material antes de entregar. O histórico fica em
memória e some quando o servidor reinicia (os arquivos ficam em `output/diarizacao/jobs/<id>/`).
Documentação da API em `/api/docs`.

## Saídas

| Pasta | Conteúdo |
|---|---|
| `output/diarizacao/reports/` | JSON, Markdown e alinhamento palavra a palavra por arquivo |
| `output/diarizacao/audio/` | Áudios intermediários (regeneráveis) |
| `output/diarizacao/jobs/` | Uploads e relatórios da interface web, um diretório por job |
| `output/benchmark/` | CSV, JSON e Markdown dos tratamentos da fase 1 |

## Arquitetura

Organização e padrões de código estão em [CLAUDE.md](CLAUDE.md).
