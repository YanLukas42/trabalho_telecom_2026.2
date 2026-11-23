# Trabalho Telecom 2026.2 — Áudio para Transcrição e Diarização com Gemini

Pesquisa em telecomunicações sobre como a compressão e o pré-processamento de áudio afetam a transcrição e a
separação de falantes pela API do Google Gemini, com foco em reduzir custo (tokens) e banda sem perder qualidade.

## Fases

- **Fase 1 — benchmark de MP3:** varredura de bitrate, taxa de amostragem, canal, filtros, VAD e ganho. Mede WER/CER,
  tokens, latência e custo. Ver [relatorio_avancos_fase1.md](relatorio_avancos_fase1.md).
- **Fase 2 — diarizador:** envia o áudio inteiro ao Gemini numa chamada e recebe o JSON no esquema padrão. Com VAD
  opcional, os tempos voltam para a linha do tempo original. O áudio enviado precisa caber em 20 MB (Opus 16 kbps cabe em ~2h50).

## Requisitos e variáveis (`.env`, nunca no git)

- **Python 3.12** (sem container e sem Docker no ambiente local)
- **FFmpeg e FFprobe** instalados no sistema (`PATH`)
- Variáveis no `.env` (use [`.env.example`](.env.example) como base):

```
GEMINI_API_KEY=...              # obrigatória
GEMINI_MODEL=gemini-2.5-flash   # opcional (padrão gemini-2.5-flash)
PAUTA_DB_PATH=output/pauta.db   # opcional (caminho do SQLite)
PAUTA_COOKIE_SECURE=0           # 0 no localhost, 1 com HTTPS
```

- `HF_TOKEN`: **não usar** no MVP (reservado apenas para o motor local `pyannote/whisper`).
- **Atenção:** o servidor escuta apenas em `127.0.0.1`. Nunca abra para a rede sem HTTPS na frente, pois senhas e aulas trafegariam sem criptografia.

## Como rodar localmente (sem Docker)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m telecom.cli.serve --port 8010
.venv/bin/python -m pytest -q
```

### Criar escola e usuários (CLI administrativa)

```bash
python -m telecom.cli.admin create-tenant "Escola X" --minutes 600
python -m telecom.cli.admin create-user --tenant <tenant_id> --email ana@escola.com --name "Ana" --role owner
python -m telecom.cli.admin reset-password --email ana@escola.com
```

```bash
# Diarização via CLI (usa videoplayback.mp4, 999.mp4 ou a primeira mídia de input/)
python -m telecom.cli.diarize
python -m telecom.cli.diarize --file input/aula.mp4 --codec opus --vad

# Benchmark: diarizacao (fase 2) ou mp3 (fase 1). --dry-run não chama a API.
python -m telecom.cli.benchmark diarizacao --dry-run
python -m telecom.cli.benchmark mp3 --file input/aula.mp4 --ground-truth referencia.json
```

## Interface web (MVP: Pauta)

```bash
.venv/bin/python -m telecom.cli.serve --port 8010   # http://127.0.0.1:8010
```

Pensada para professores de inglês e escolas (multi-tenant). Fluxo:

1. **Entrar e Minhas aulas (`#/entrar`, `#/`):** entre com sua conta; a página inicial lista suas aulas com duração, situação, cota mensal de minutos e confirmação LGPD para excluir.
2. **Enviar gravação (`#/nova`):** informe o arquivo (até 300 MB e até 3 h) e marque o consentimento obrigatório (com aviso de uso do Google Gemini).
3. **Aula (`#/aulas/<id>`):** ouça a gravação, confirme quem é professor e alunos (salvo no servidor) e pesquise na transcrição.
4. **Atividades (`#/aulas/<id>/atividades`):** escolha nível (A1–C2), número de atividades e foco; revise ou edite erros, enunciados e respostas antes de imprimir ou salvar em PDF.
5. **Próxima aula (`#/aulas/<id>/proxima`):** visualize e imprima o roteiro com objetivo, etapas cronometradas e tarefa de casa.

A IA lê só o texto da transcrição, sem ouvir o áudio: confira o material antes de entregar. As sessões, nomes, materiais e eventos de uso ficam salvos no SQLite (`output/pauta.db`) e os arquivos por escola em `output/tenants/<tenant_id>/sessions/<session_id>/`.
Documentação da API v1 em `/api/v1/docs`.

### Navegadores suportados e PDF

- **Navegadores:** Chrome, Edge, Firefox e Safari nas **2 últimas versões** (a interface usa `<ruby>`, CSS `:has()` e módulos ES nativos).
- **PDF:** gerado diretamente pelo navegador em **"Imprimir → Salvar como PDF"** (sem biblioteca externa de PDF).

## Referência de deploy em VPS (futuro — não aplicar agora)

- **Máquina base:** Ubuntu 24.04, 2 vCPU, 4 GB RAM, 40 GB de disco, Python 3.12, FFmpeg, domínio configurado e firewall permitindo apenas portas `80`, `443` e SSH.
- **Processo + Proxy:** `uvicorn` com **1 worker** gerenciado via `systemd` escutando em `127.0.0.1`, com **Caddy** na frente (HTTPS automático, `reverse_proxy` e `request_body { max_size 320MB }`).
- **Configuração e backup:** `PAUTA_COOKIE_SECURE=1`; backup diário do SQLite (`sqlite3 pauta.db ".backup backup.db"`) e da pasta `output/tenants/`, com restauração testada ao menos uma vez.
- **Alternativa com Docker (referência):** imagem `python:3.12-slim` + `apt install ffmpeg`, usuário sem `root`, volumes persistentes para o SQLite e `output/`, expondo a porta `8000` apenas para o Caddy (nunca publicada externamente).
- **Crescendo:** migrar para PostgreSQL 16 (com *Row Level Security*) + fila e *worker* separados, seguindo os ADRs.

## Documentação

- [Histórias de usuário](docs/produto/historias-de-usuario.md) e [regras de negócio](docs/produto/regras-de-negocio.md)
- [Identidade visual](docs/identidade-visual/README.md)
- [Arquitetura](docs/arquitetura/README.md), [multi-tenancy](docs/arquitetura/multitenancia.md), [segurança](docs/arquitetura/seguranca.md), [ADRs](docs/arquitetura/adr/) e [plano dos PRs](docs/arquitetura/plano-prs-mvp.md)

## Saídas

| Pasta / Arquivo | Conteúdo |
|---|---|
| `output/pauta.db` | Banco SQLite (escolas, usuários, sessões de aula, uso e auditoria) |
| `output/tenants/` | Mídias, relatórios e materiais separados por `<tenant_id>/sessions/<session_id>/` |
| `output/diarizacao/reports/` | JSON, Markdown e alinhamento palavra a palavra gerados via CLI |
| `output/diarizacao/audio/` | Áudios intermediários (regeneráveis) |
| `output/benchmark/` | CSV, JSON e Markdown dos tratamentos da fase 1 |

## Arquitetura

Organização e padrões de código estão em [CLAUDE.md](CLAUDE.md).
