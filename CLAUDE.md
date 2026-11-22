# Padrões do projeto

Projeto de pesquisa: otimização de áudio para transcrição e diarização com Gemini. O código é pequeno e
precisa continuar fácil de manter. Antes de criar algo novo, procure o módulo que já resolve o problema.

## Estrutura

```
telecom/
  settings.py        configuração: caminhos, .env, tarifas (não cria diretórios nem grava arquivos)
  timefmt.py         formatação de tempos
  reporting.py       escrita de CSV/JSON/Markdown
  experiments.py     matrizes de tratamentos (dados, não código)
  audio/             FFmpeg e processamento de áudio
    ffmpeg.py        ÚNICO módulo que executa FFmpeg/FFprobe
    codecs.py        estratégias de codec (mp3, opus)
    filters.py       cadeias de filtros -af
    silence.py       detecção de silêncio (silencedetect)
    vad.py           SpeechMap: remoção de pausas com mapa de tempo
    preparer.py      Treatment (dado) + prepare_audio (execução)
  asr/               integração com o Gemini
    gemini.py        ÚNICO módulo que chama a API
    schemas.py       esquemas Pydantic de saída
    repair.py        recuperação de JSON truncado
  metrics/           WER/CER, custo, compressão
  diarization/       pipeline de diarização
    pipeline.py      orquestração
    transcriber.py   GeminiDiarizer: envia o áudio inteiro numa chamada
    pyannote_whisper.py  diarização local: pyannote (turnos) + whisper (palavras); deps pesadas importadas tardiamente
    timeline.py      alinhamento turno x palavra (funções puras)
    alignment.py     palavra a palavra
    report.py        montagem de JSON/Markdown (funções puras)
    prompts.py       prompts
    models.py        contratos (Diarizer, Transcription, Turn, WordTiming, SpeakerWord)
    factory.py       build_diarizer e disponibilidade dos motores; usado pela CLI e pela web
    review.py        revisão por IA, só texto: nomes dos falantes e possíveis erros
  benchmark/         motor único de benchmark (fase 1 e fase 2)
  lessons/           material de aula para professores de inglês
    materials.py     contrato (LessonMaterials), prompt, validação (funções puras) e GeminiLessonWriter
  web/               interface web local (MVP do SaaS "Pauta": aula gravada → atividades por aluno + plano)
    jobs.py          JobService: fila em memória, pipeline injetado por fábrica; guarda o material do job
    app.py           create_app: rotas FastAPI e arquivos estáticos; gerador de material injetado
    schemas.py       contratos da API
    static/          HTML, CSS e JS puros, sem build; PDF pelo "imprimir" do navegador (CSS @media print)
  cli/               pontos de entrada (diarize, benchmark, serve)
tests/               pytest; espelha os módulos
```

**Direção das dependências:** `settings`/`timefmt` ← `audio` ← `diarization`/`benchmark`/`lessons` ← `web` ← `cli`.
`asr` é usado por `diarization`, `benchmark` e `cli`. Um módulo de nível baixo nunca importa um de nível alto:
`audio` não conhece `asr`, `diarization` ou `benchmark`.

## Padrões de projeto usados

- **Strategy:** `AudioCodec` (`Mp3Codec`, `OpusCodec`) escolhido por `get_codec(name)`. Novo codec = nova subclasse
  e uma entrada em `_CODECS`.
- **Injeção de dependência por Protocol:** `DiarizationPipeline` recebe um `Diarizer`, `BenchmarkEngine`
  recebe um `AudioTranscriber`, e `JobService` recebe uma fábrica de pipeline (montada em `cli/serve.py`). Testes usam fakes. Nunca chame a API nos testes.
- **Objetos de valor imutáveis:** `@dataclass(frozen=True)` para `Treatment`, `SpeechMap`, `AudioChunk`,
  `Transcription`, `GenerationResult`.
- **Funções puras para a lógica:** `SpeechMap.from_silences`, `parse_chunk_json`,
  `build_payload`, `render_markdown`. A lógica fica sem I/O para ser testada direto.
- **Ponto único de contato:** FFmpeg só em `audio/ffmpeg.py`, Gemini só em `asr/gemini.py`.
- **Dados em vez de código:** tratamentos são `Treatment` em `experiments.py`. Um novo experimento é uma linha.

## Regras

- **Imports absolutos** a partir de `telecom`. Não manipule `sys.path`. Rode módulos com `python -m` na raiz.
- **Sem efeitos colaterais ao importar:** nada de `mkdir`, leitura de arquivo ou `print` no nível do módulo.
  Crie diretórios sob demanda, dentro da função que escreve.
- **Logging com `logging`**, não `print`. A CLI configura o log (`cli/common.py`).
- **Erros explícitos:** lance `FFmpegError` ou `ValueError`. Não devolva `0.0` nem `None` escondendo falha.
  Resposta inválida do Gemini (JSON ilegível ou fora do esquema) lança `ValueError`. Nunca grave relatório vazio.
- **Tipos:** anotações em funções públicas. Use `X | None` e `list[str]` (Python 3.10+).
- **Sem números mágicos:** constantes nomeadas no topo do módulo (ex.: `DEFAULT_PAD_SEC`, `MAX_OUTPUT_TOKENS`).
- **Revisão por IA não ouve o áudio:** um nome só entra se a evidência literal existir no texto. Correções são sugestões.
- **Alinhamento pyannote x whisper:** os dois leem o mesmo arquivo, sem recorte. Palavras sem turno viram `desconhecido`,
  e o aviso de deslocamento vai para `alinhamento.avisos`.
- **Diarização Gemini é uma chamada só:** o áudio inteiro vai ao Gemini. Não há paralelismo nem fatiamento. Dados inline da API têm teto de 20 MB.
- **Dependências:** só o que está em `requirements.txt`. Antes de adicionar uma lib, confirme que a stdlib não resolve.
- **Idioma:** identificadores em inglês. Docstrings, mensagens de log e textos para o usuário em português.
  Chaves dos JSON de saída, prompts e descrições dos esquemas ficam em português: são contrato com os relatórios
  já gerados e com o modelo. Não renomeie sem reavaliar a saída.
- **Web sem estado persistente:** jobs vivem em memória (`JobService`); arquivos em `output/diarizacao/jobs/<id>/`.
  Chaves do envelope do job em inglês (contrato novo); o `result` é o JSON do relatório, em português, sem alteração.
- **Arquitetura e segurança:** siga `docs/arquitetura/` (regras `AR`, `PD`, `MT`, `TN`, `SG`). `tests/test_architecture.py`
  verifica a direção das dependências, os pontos únicos de contato (FFmpeg, Gemini), `print` fora da CLI, tamanho de arquivo
  e JS sem HTML injetado; pacote novo entra em `LAYER` antes de existir. Nunca registre em log texto de fala, nome de aluno
  ou nome de arquivo do usuário. Acesso a dado de cliente sempre com o tenant (hoje ainda não há tenant: ver fase 1).
  Dependência nova exige ADR em `docs/arquitetura/adr/`.
- **Produto:** histórias e regras em `docs/produto/` (códigos `RN-xx`). Mudou uma regra no código? Atualize a tabela
  de regras e a situação da história. Regra nova de negócio entra com código `RN` novo.
- **Identidade visual:** ao mexer em `web/static/`, siga `docs/identidade-visual/README.md` (tokens no `styles.css`).
  Vermelho só para correção de erro de inglês; textos em português, com os nomes fixos do guia.
- **Material de aula só com texto:** a IA não ouve o áudio. Um erro de aluno só entra se a citação existir literalmente
  nas falas dele (`validated_materials`). A interface avisa que o professor deve conferir antes de entregar.
  O PDF sai do `window.print()` com `#print-root`; não adicione biblioteca de PDF. O pedido de material e o
  `lesson` do job são contrato novo, com chaves em inglês.
- **Arquivos de saída:** diarização grava em `output/diarizacao/`, benchmark em `output/benchmark/`.
  Nunca grave fora de `output/`.

## Testes

- `python -m pytest` roda tudo. Os testes que usam FFmpeg são pulados se ele não existir.
- Lógica pura é testada diretamente. Integração usa o fixture `speech_wav` (áudio sintético gerado pelo FFmpeg).
- Ao mudar o comportamento de um módulo, atualize o teste do mesmo nome em `tests/`.

## Ao mexer no código

- Mudou a saída (JSON, Markdown, CSV)? Diga explicitamente que o contrato mudou e por quê.
- Não versione `.env`, `input/*` ou `output/benchmark/*`. Áudios intermediários em `output/diarizacao/audio/`
  são regeneráveis e estão no `.gitignore`.
- Não faça commit sem pedido explícito.
