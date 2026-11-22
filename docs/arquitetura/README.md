# Arquitetura da Pauta

**Persona deste documento:** arquiteto de software sênior de um SaaS B2B educacional, responsável por manter o produto
pequeno, seguro e barato de evoluir enquanto ele passa de ferramenta local para serviço multi-tenant. As regras abaixo são
opinião de arquiteto: cada uma diz o que fazer, por quê e como se verifica. Onde o código de hoje não cumpre, a lacuna
está escrita, não escondida.

Documentos irmãos: [multi-tenancy](multitenancia.md) · [segurança](seguranca.md) ·
[regras de negócio](../produto/regras-de-negocio.md) · [CLAUDE.md](../../CLAUDE.md) (convenções de código do dia a dia).

## Como ler

- **DEVE** é inegociável: quebrar exige um ADR (registro de decisão) aprovado. **DEVERIA** é o padrão: desvio exige
  justificativa no PR. **PODE** é permissão.
- Cada regra tem código: `AR` (arquitetura), `PD` (padrões de projeto), `MT` (manutenibilidade), `TN` (tenancy),
  `SG` (segurança). Cite o código no PR e no teste.
- A marca **[teste]** significa que a regra é verificada automaticamente em
  [`tests/test_architecture.py`](../../tests/test_architecture.py). As demais dependem de revisão: use a
  [lista de revisão](#lista-de-revisão-de-pr).

## Onde estamos e para onde vamos

**Hoje (fase 0):** monólito modular em Python, um processo, um usuário, na máquina do professor. Fila de jobs e histórico em
memória; arquivos em `output/`. Sem login. Dependências bem separadas por Protocol (diarizador, revisor, gerador de
material, fábrica de pipeline), o que torna a evolução barata.

**Alvo:** o mesmo monólito modular, agora com persistência, identidade e isolamento por organização (tenant), e com o
trabalho pesado fora do processo web. **Não vamos para microsserviços**: a equipe é pequena, o domínio é um fluxo só, e o
custo de operar serviços distribuídos supera qualquer ganho antes de milhares de tenants. O limite entre módulos já é
vigiado por teste; se um dia um módulo precisar sair, ele sai com o contrato pronto.

```
Navegador (HTML, CSS e JS puros)
   │ HTTPS
┌──▼───────────────────────────────────────────────────────┐
│ web/        rotas finas: autentica, resolve o tenant,    │  adaptador de entrada
│             valida e delega                              │
├──────────────────────────────────────────────────────────┤
│ application/ casos de uso: transcrever aula, gerar       │  (a criar na fase 1)
│             material, excluir aula. Recebem o tenant      │
├──────────────────────────────────────────────────────────┤
│ diarization/ lessons/ audio/   domínio e regras puras    │  funções puras e objetos de valor
├──────────────────────────────────────────────────────────┤
│ Portas (Protocol): Diarizer, LessonWriter, SessionRepo,  │
│ BlobStore, JobQueue, UsageMeter, Clock                   │
└──┬───────────┬───────────┬───────────┬──────────┬────────┘
 Gemini      FFmpeg     Postgres    Armazenamento  Fila
 (asr/)     (audio/)    (com RLS)   de objetos     (worker separado)
```

## Regras de arquitetura

| Código | Regra | Por quê |
|---|---|---|
| AR-01 | **DEVE** respeitar a direção das dependências: `settings`/`timefmt`/`reporting` ← `audio`/`asr`/`metrics` ← `experiments` ← `diarization`/`benchmark` ← `lessons` ← `web` ← `cli`. Pacotes irmãos não se importam. Um pacote novo entra em `LAYER` no teste de arquitetura antes de existir. **[teste]** | Sem isso o código vira uma bola de lama em seis meses. Hoje está limpo: todo o teste passa sem exceção. |
| AR-02 | **DEVE** haver um ponto único de contato com cada sistema externo: FFmpeg só em `audio/ffmpeg.py`, Gemini só em `asr/gemini.py`. Banco, armazenamento de objetos e fila terão o seu, cada um atrás de uma porta. **[teste para FFmpeg e Gemini]** | Trocar de fornecedor, limitar custo, medir uso e proteger segredo acontecem em um lugar só. |
| AR-03 | **DEVE** haver composição só na borda: as dependências concretas são montadas em `cli/serve.py` (e no futuro no *worker*), e injetadas por Protocol. Nenhum módulo de domínio instancia cliente de API, conexão ou relógio. | Testa-se tudo com fakes, sem rede e sem API. |
| AR-04 | **DEVE** haver separação entre rota HTTP e caso de uso: a rota valida e traduz erro; o caso de uso decide. Quando a primeira regra de negócio com mais de um passo ou com tenant aparecer em `web/app.py`, ela vai para `application/`. | Rotas gordas são intestáveis e prendem a lógica ao FastAPI. |
| AR-05 | **DEVE** o domínio ser puro: regras e validações recebem dados e devolvem dados, sem I/O (`validated_materials`, `guessPeople` equivalente no servidor, `SpeechMap.from_silences`). O I/O fica nas bordas. | É o que torna as regras testáveis em milissegundos e reaproveitáveis no worker. |
| AR-06 | **DEVE** o trabalho pesado (transcrição, geração de material) rodar fora do processo da API quando houver mais de um usuário simultâneo. A API enfileira e responde `202`; o *worker* executa. Hoje usa `ThreadPoolExecutor` e isso é aceitável só na fase 0. | Uma transcrição de uma hora não pode derrubar ou travar o atendimento dos outros tenants. |
| AR-07 | **DEVE** todo job ser **idempotente e retomável**: reexecutar o mesmo `session_id` não duplica custo nem resultado. Chave de idempotência na criação (`Idempotency-Key`) e estado em máquina de estados (PD-05). | Filas entregam "pelo menos uma vez". Sem idempotência, uma reentrega cobra duas vezes do Gemini. |
| AR-08 | **DEVE** o estado viver fora do processo (banco, armazenamento de objetos). O processo da API é descartável e pode ter N réplicas. | Escalar e fazer deploy sem perder aulas. Hoje não vale: o histórico está em memória. |
| AR-09 | **DEVERIA** toda chamada a sistema externo ter timeout, repetição com recuo exponencial e limite de tentativas, e erro traduzido para um erro do domínio (`ValueError`, `FFmpegError`). O Gemini já tem repetição; o FFmpeg não tem timeout (ver lacunas em [segurança](seguranca.md)). | Um processo pendurado consome um worker para sempre. |
| AR-10 | **DEVERIA** a configuração vir só do ambiente (12-factor), lida em `settings.py` sem efeitos colaterais na importação, e com a lista das variáveis obrigatórias validada na subida do serviço. | Falhar na subida é melhor do que falhar na primeira aula de um cliente. |
| AR-11 | **DEVE** o contrato público ser versionado: rotas sob `/api/v1`, esquemas Pydantic explícitos. Campo novo é aditivo; remover ou renomear exige nova versão. O `result` do relatório (chaves em português) não muda sem reavaliar os relatórios gerados. | Clientes antigos continuam funcionando durante a migração. |
| AR-12 | **DEVE** a camada de apresentação (HTML, CSS e JS) tratar todo texto vindo de aluno ou de IA como dado: só `createTextNode`/`textContent`. **[teste]** | Transcrição e saída de modelo são entrada não confiável (ver SG-09). |

## Padrões de projeto

Padrão é ferramenta: usa-se onde resolve um problema que já existe, e não antes. Para cada um, onde está, quando usar e quando
não.

| Código | Padrão | Onde está / vai entrar | Use quando | Não use quando |
|---|---|---|---|---|
| PD-01 | **Portas e adaptadores** (Protocol) | `Diarizer`, `TranscriptReviewer`, `LessonWriter`, `PipelineFactory`. Entram: `SessionRepository`, `BlobStore`, `JobQueue`, `UsageMeter`, `Clock`. | Há um sistema externo ou uma escolha de implementação que o teste precisa trocar. | Só existe uma implementação e nenhuma razão para uma segunda. |
| PD-02 | **Strategy** | `AudioCodec` (`get_codec`), motores de diarização (`ENGINES`). | Um comportamento varia por configuração e todas as variantes têm a mesma forma. | A variação é um `if` de uma linha. |
| PD-03 | **Factory** | `build_diarizer`, `build_pipeline`, `lesson_writer_factory`. | A criação tem custo (cliente de API, modelo pesado) ou depende de configuração, e deve ser adiada. | O construtor já basta. |
| PD-04 | **Repositório** | A criar na fase 1: `SessionRepository` no lugar do dicionário de `JobService`. Toda assinatura recebe o tenant (TN-03). | Persistência de uma entidade com regra de acesso. | Dados de leitura única, sem identidade. |
| PD-05 | **Máquina de estados** | `JobStatus`. Passar a validar as transições permitidas (queued → processing → done/failed) e proibir as demais. | O objeto tem ciclo de vida com regras de transição. | Um sinalizador booleano resolve. |
| PD-06 | **Objeto de valor imutável** | `@dataclass(frozen=True)`: `Treatment`, `SpeechMap`, `Transcription`, `LessonRequest`, `Participant`. Identificadores tipados na fase 1 (`TenantId`, `SessionId` como `NewType`). | Dados que se comparam por conteúdo e não mudam. | Entidade com identidade e ciclo de vida. |
| PD-07 | **Camada anticorrupção** | Esquemas Pydantic do Gemini (`TranscricaoChunkDiarizada`, `LessonMaterials`) validados e convertidos para tipos do domínio antes de entrar. | Dados de fora que podem vir errados ou mudar de forma. | Dados que o próprio sistema produziu. |
| PD-08 | **Decorator** (política transversal) | A criar: embrulhar `GeminiClient` com medição de uso por tenant e com limite de custo, sem mexer nos chamadores. | Aspecto transversal (cota, métrica, cache) que muitos chamadores precisam. | Lógica específica de um único caso de uso. |
| PD-09 | **Comando + fila** | Cada job é um comando (`tenant_id`, `session_id`, opções) serializável. | Trabalho assíncrono que pode ser repetido. | Chamada síncrona curta. |
| PD-10 | **Função pura primeiro** | `build_payload`, `render_markdown`, `parse_materials`. | Sempre que a regra não precisar de I/O. | — |

**Evitar:** singleton global e estado de módulo mutável (esconde dependência e quebra testes paralelos); herança profunda
(use composição); localizador de serviço; ORM "mágico" que faz consulta sem o tenant; classes "gerente" que sabem de tudo;
abstração para um caso só; microsserviço sem dor que o justifique.

## Manutenibilidade

| Código | Regra |
|---|---|
| MT-01 | **DEVE** arquivo Python ter no máximo 400 linhas, e função no máximo ~40. Acima disso, divida por responsabilidade. O limite do JS é o mesmo, com uma dívida registrada: `app.js` tem 909 linhas e o teto de 950 só pode diminuir. **[teste]** Próximo passo: dividir em módulos ES (`<script type="module">`, sem build). |
| MT-02 | **DEVE** toda função pública ter anotação de tipo (`X \| None`, `list[str]`). Novo código passa em verificador de tipos quando o projeto o adotar (ADR). |
| MT-03 | **DEVE** erro ser explícito: lançar `ValueError` ou `FFmpegError`, nunca devolver `0.0` ou `None` escondendo falha, nunca engolir exceção. Quem captura traduz e registra. |
| MT-04 | **DEVE** haver teste para todo comportamento novo, no arquivo de teste espelho. Lógica pura é testada direto; integração usa fakes; **a API real nunca é chamada em teste**. Corrigiu um bug? Primeiro um teste que falha. |
| MT-05 | **DEVERIA** preferir fakes escritos à mão a *mocks* que replicam a implementação. O fake obedece ao Protocol e vira reaproveitável (`FakeDiarizer`, `FakeLessonWriter`). |
| MT-06 | **DEVE** nenhum número mágico: constante nomeada no topo do módulo (`MAX_CONCURRENT_JOBS`, `MIN_CONFIDENCE`). Regra de negócio com número aparece também em [regras-de-negocio.md](../produto/regras-de-negocio.md) com o código `RN`. |
| MT-07 | **DEVE** não haver efeito colateral na importação: sem ler arquivo, sem criar diretório, sem `print`. Diretórios nascem sob demanda, dentro de quem grava. **[teste para `print`]** |
| MT-08 | **DEVE** uma dependência nova só entrar depois de confirmar que a biblioteca padrão não resolve, e com um ADR de uma página (necessidade, alternativas, custo de manutenção, licença). Versões com limite inferior e superior; atualização regular. |
| MT-09 | **DEVERIA** comentário explicar o *porquê*, não o *quê*. Docstring em português, identificador em inglês. Comentário que repete o código sai. |
| MT-10 | **DEVE** decisão estrutural virar ADR curto em `docs/arquitetura/adr/NNNN-titulo.md`: contexto, decisão, consequências, alternativas descartadas. ADR não se apaga: é substituído por outro. |
| MT-11 | **DEVE** dívida técnica ser registrada com dono e gatilho (como o teto do `app.js`), e nunca silenciada. |
| MT-12 | **DEVERIA** commits pequenos, no formato `tipo(escopo): mensagem` (`feat`, `fix`, `refactor`, `docs`, `test`), e cada PR fazer uma coisa. Mudou saída (JSON, Markdown, CSV, API)? O PR diz que o contrato mudou e por quê. |
| MT-13 | **DEVE** o merge exigir a suíte verde. Quando houver integração contínua: `pytest`, teste de arquitetura, varredura de dependências (SG-14) e verificação de formatação. Nenhum desses é "opcional". |
| MT-14 | **DEVERIA** logs estruturados com `tenant_id`, `session_id` e `request_id`, e **nunca** com texto de fala, nome de aluno ou segredo (SG-11). |

## Roteiro de evolução

Cada fase tem um critério de saída observável. Só se começa a seguinte quando o anterior vale.

| Fase | Entrega | Critério de saída |
|---|---|---|
| **0. Hoje** | Monólito modular local; jobs em memória; sem login. | 227 testes verdes; arquitetura limpa. |
| **1. Persistência e identidade** | `application/`; `SessionRepository` e `BlobStore` (portas); banco; login por provedor OIDC; limite de upload e de tamanho; timeout no FFmpeg; ID de 128 bits; `/api/v1`; teste de isolamento entre usuários. | Reiniciar o servidor não perde aulas. Um usuário nunca vê a aula de outro, provado por teste. |
| **2. Multi-tenant** | `tenant_id` em tudo; RLS no banco; fila e *worker* separados; cotas e medição de uso por tenant; auditoria; exclusão e exportação (LGPD); papéis por organização. | Dois tenants sob carga: o lento não atrasa o outro. Teste automático de isolamento passa em todas as rotas. |
| **3. Escala e enterprise** | Isolamento dedicado opcional; chave própria do cliente; SSO/SAML; residência de dados; SLA e DR testado. | Restauração de backup medida e dentro de RPO/RTO. |

## Lista de revisão de PR

Responda *sim*, *não se aplica* ou justifique:

**Arquitetura e manutenção**
- [ ] A dependência aponta para baixo, e o teste de arquitetura passa (AR-01, AR-02)?
- [ ] A regra de negócio está numa função pura, com teste, e a constante tem nome (AR-05, MT-04, MT-06)?
- [ ] Mudou contrato (API, JSON, CSV)? O PR diz e a versão acompanha (AR-11)?
- [ ] Mudou regra de negócio? `regras-de-negocio.md` e a história foram atualizadas?
- [ ] Nova dependência: há ADR e a stdlib realmente não resolve (MT-08)?

**Segurança e tenant**
- [ ] Todo acesso a dado passa pelo tenant do chamador, e nunca por um ID sozinho (TN-03)?
- [ ] Recurso de outro tenant responde 404 e há teste cobrindo (TN-04, TN-12)?
- [ ] Entrada validada (tamanho, tipo, tamanho de texto) e saída de IA validada contra esquema (SG-06, SG-09)?
- [ ] Algum log, erro ou métrica carrega conteúdo de fala, nome de aluno ou segredo (SG-11)?
- [ ] Chamada a sistema externo tem timeout, limite de custo e tratamento de erro (AR-09, TN-09)?

## ADRs a registrar

Decisões já tomadas neste documento, mas que precisam do registro formal quando forem implementadas:

1. Monólito modular em vez de microsserviços.
2. Multi-tenancy em banco compartilhado com RLS, com opção de isolamento dedicado (ver [multi-tenancy](multitenancia.md)).
3. Provedor de identidade externo (OIDC) em vez de senha própria.
4. Fila e *worker* para o trabalho pesado; escolha da tecnologia da fila.
5. Armazenamento de objetos para áudio e material; URLs assinadas.
6. Verificador de tipos e *linter* (dependências de desenvolvimento).
