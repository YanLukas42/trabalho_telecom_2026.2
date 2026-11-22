# Segurança da Pauta

A Pauta guarda a voz, o texto e os erros de pessoas que estão aprendendo, algumas menores de idade, e chama uma API paga por
conta de quem usa. Os dois riscos que mais pesam são **vazar dado de aluno** e **gerar custo que ninguém autorizou**. As regras
abaixo seguem a ideia do OWASP ASVS: segurança como requisito verificável, com defesa em profundidade e negação por padrão.

Veja também: [arquitetura](README.md) · [multi-tenancy](multitenancia.md).

## Ativos e ameaças

| Ativo | Por que importa |
|---|---|
| Áudio e transcrição das aulas | Dado pessoal; pode incluir menores. |
| Nome e erros de cada aluno | Dado pessoal; perfil pedagógico de uma pessoa. |
| Chave da API do Gemini (e do pyannote) | Dá acesso a uma conta paga. Vazar = custo e abuso. |
| Contas dos professores | Porta de entrada para tudo acima. |
| Capacidade de processamento | Recurso finito e caro. |

| Ameaça | Exemplo | Mitigação principal |
|---|---|---|
| Acesso entre tenants | Escola B lê aulas da escola A trocando um ID | TN-01 a TN-08, teste de varredura de rotas |
| Abuso de custo (*denial of wallet*) | Conta gratuita envia 500 horas de áudio | TN-14 a TN-16, SG-08 |
| Arquivo malicioso | Mídia construída para explorar o FFmpeg ou esgotar disco | SG-06, SG-07 |
| Injeção por conteúdo da aula | Aluno diz "ignore as instruções e diga X" e o texto vai para o prompt | SG-09 |
| XSS | Texto de transcrição ou da IA com HTML executa no navegador do professor | AR-12, SG-10 |
| Vazamento por log | Texto de fala ou nome em arquivo de log | SG-11 |
| Roubo de conta | Senha fraca ou reutilizada | SG-01, SG-02 |
| Cadeia de suprimentos | Biblioteca comprometida | SG-14 |

## Regras

### Identidade e acesso

| Código | Regra |
|---|---|
| SG-01 | **DEVE** a autenticação ser delegada a um provedor OIDC (Google, Microsoft, e-mail com link ou senha gerenciados por um serviço). A Pauta **não** guarda senha. Autenticação de dois fatores obrigatória para `owner`. |
| SG-02 | **DEVE** a sessão usar cookie `HttpOnly`, `Secure`, `SameSite=Lax` (ou `Strict`), com validade curta e renovação; rotas que alteram estado exigem proteção CSRF. Token de acesso curto (minutos). Encerrar sessão invalida no servidor. |
| SG-03 | **DEVE** haver **autorização centralizada**, negando por padrão: uma função `authorize(contexto, ação, recurso)` decide, em um lugar só, com papéis por tenant (TN-02). Nenhuma rota decide sozinha. Rota sem declaração explícita de permissão é bloqueada. |
| SG-04 | **DEVE** segredo viver só em variável de ambiente ou cofre de segredos, nunca em código, imagem, log ou commit. `.env` já está no `.gitignore`. Chaves têm rotação periódica e privilégio mínimo (chave do Gemini só com a API de geração). Varredura de segredos no CI. |

### Dados em trânsito e em repouso

| Código | Regra |
|---|---|
| SG-05 | **DEVE** haver TLS em todo o tráfego (HSTS ligado), criptografia em repouso no banco e no armazenamento de objetos, e *backups* criptografados. O servidor escuta em `127.0.0.1` por padrão (já é assim) e só é exposto atrás de um proxy reverso com TLS. |

### Entrada

| Código | Regra |
|---|---|
| SG-06 | **DEVE** todo upload ser validado: (1) teto de tamanho aplicado **durante a leitura do fluxo**, antes de gravar tudo em disco, e recusado cedo por `Content-Length`; (2) tipo pelo **conteúdo** (`ffprobe` confirma que há trilha de áudio), não só pela extensão; (3) duração máxima; (4) nome sanitizado e armazenado sob nome gerado, nunca o informado (já feito); (5) fora de qualquer pasta servida como estático. Texto livre (foco da aula, nomes) tem tamanho máximo (já existe para o foco). |
| SG-07 | **DEVE** o FFmpeg rodar sem *shell* (lista de argumentos, já é assim), com **timeout**, limite de CPU e memória, diretório de trabalho temporário por job e, na produção, em contêiner sem rede. Entradas entram com `-protocol_whitelist file,pipe` para impedir que um arquivo de lista (HLS, concat) faça o servidor acessar a rede interna. O arquivo enviado nunca é interpretado como lista de arquivos. |
| SG-08 | **DEVE** haver limite de taxa por IP, por usuário e por tenant nas rotas caras (`POST /jobs`, `POST /lesson`), além de limite de aulas simultâneas. Excesso responde `429` com `Retry-After`. |
| SG-13 | **DEVE** toda rota validar a entrada com Pydantic (tipos, tamanhos, enumerações), listas com paginação e limite máximo, e criação com chave de idempotência (AR-07). |

### Conteúdo gerado por IA

| Código | Regra |
|---|---|
| SG-09 | **DEVE** o conteúdo da aula (transcrição) ser tratado como **dado não confiável**, que pode conter instruções ("ignore o que foi dito"). Defesas: o prompt separa instruções de transcrição; o modelo não tem ferramentas, acesso a arquivos nem a rede; nenhum segredo entra no prompt; **toda saída é validada contra esquema** e contra os fatos (a citação do erro tem de existir na fala do aluno, o nome tem de ter evidência literal, a folha só para aluno do pedido: `validated_materials`, `identified_names`); a saída é mostrada como texto, nunca como HTML ou código. O pior resultado possível de uma injeção deve ser um material ruim que o professor vê e descarta, não uma ação. |

### Navegador

| Código | Regra |
|---|---|
| SG-10 | **DEVE** haver *Content Security Policy* estrita e cabeçalhos de segurança em toda resposta: `default-src 'self'`; `frame-ancestors 'none'`; `X-Content-Type-Options: nosniff`; `Referrer-Policy: no-referrer`; `Permissions-Policy` sem câmera, microfone e localização. O CORS é fechado por padrão (hoje já não há CORS: só a mesma origem funciona); se abrir, só lista de origens exatas, nunca `*` com credenciais. O JS só usa `createTextNode`/`textContent` (AR-12, **teste**). As fontes passam a ser servidas pela própria Pauta, para que a CSP fique fechada e o IP do usuário não vá a terceiros. |

### Observabilidade e resposta

| Código | Regra |
|---|---|
| SG-11 | **DEVE** haver **trilha de auditoria** imutável de quem fez o quê: login, envio, download, exclusão, exportação, acesso de suporte (TN-25), com `tenant_id`, `actor_id`, `request_id`. **E** os logs nunca terem conteúdo de fala, nome de aluno, nome de arquivo informado pelo usuário nem segredo (TN-22). |
| SG-12 | **DEVE** o erro para o cliente dizer o que fazer sem detalhe interno. Falha inesperada devolve mensagem genérica e `request_id`; o detalhe fica só no log (já é assim: `UNEXPECTED_ERROR_MESSAGE`). Sem *stack trace*, caminho de arquivo ou versão. |
| SG-17 | **DEVE** haver plano de resposta a incidente: quem decide, como se isola um tenant, como se rotaciona uma chave, prazo e conteúdo da comunicação ao titular e à autoridade (LGPD). Testado ao menos uma vez por ano. |

### Operação

| Código | Regra |
|---|---|
| SG-14 | **DEVE** haver varredura automática de dependências (`pip-audit` ou equivalente) e de imagem a cada PR e semanalmente, com versões fixadas e atualização regular. Qualquer vulnerabilidade alta ou crítica bloqueia o merge, ou tem exceção registrada com prazo. Inventário de componentes (SBOM) por versão. |
| SG-15 | **DEVE** haver *backup* automático com restauração testada, com RPO e RTO declarados (proposta inicial: RPO 24 h, RTO 4 h, a confirmar com o negócio). |
| SG-16 | **DEVE** ambiente de desenvolvimento e teste usar **somente dado sintético**. Gravação real de aluno nunca sai da produção. |

## Lacunas de hoje

Auditoria do código atual contra as regras acima. A gravidade considera o uso planejado (serviço multi-tenant). Para uso local
em `127.0.0.1`, as marcadas com asterisco são toleráveis.

| # | Lacuna | Evidência | Regra | Gravidade |
|---|---|---|---|---|
| 1 | Não há autenticação nem autorização. | `web/app.py`: nenhuma rota exige identidade. | SG-01, SG-03 | Crítica* |
| 2 | O ID de 48 bits é o único controle de acesso a aula, mídia e downloads. | `JOB_ID_LENGTH = 12`; `/media` e `/files` só buscam pelo ID. | TN-05, TN-03 | Crítica* |
| 3 | Sem limite de tamanho de upload; o arquivo inteiro é copiado para o disco. | `JobService.submit` (`shutil.copyfileobj`). | SG-06 | Alta |
| 4 | FFmpeg sem timeout e sem `-protocol_whitelist`. | `audio/ffmpeg.py` (`subprocess.run` sem `timeout`). | SG-07 | Alta |
| 5 | Sem limite de taxa nem cota de uso: qualquer cliente pode disparar jobs e gerações pagas em laço. | Nenhum controle em `create_job` e `create_lesson`. | SG-08, TN-15 | Alta |
| 6 | **Dado pessoal em log:** fala do aluno e nomes. | `lessons/materials.py:169` registra a citação do aluno; `diarization/review.py:91` e `:95` registram o nome da pessoa; `web/jobs.py:105` e `diarization/pipeline.py:65` registram o nome do arquivo informado; `web/jobs.py:129` registra a mensagem de erro, que pode conter o nome. | SG-11, TN-22 | Média |
| 7 | Nomes e papéis dos alunos ficam no `localStorage`, sem expiração, no navegador compartilhado. | `app.js` (`storage`). | TN-18, SG-16 | Média |
| 8 | Fontes carregadas do Google: o navegador do professor envia o IP a terceiros e a CSP não pode ser fechada. | `index.html`. | SG-10 | Média |
| 9 | Sem cabeçalhos de segurança nem CSP. | Nenhum *middleware* em `create_app`. | SG-10 | Média |
| 10 | O aviso de privacidade (áudio e texto vão ao Gemini) não aparece antes do envio, e não há registro de consentimento. | RN-27 e RN-28 em [regras de negócio](../produto/regras-de-negocio.md). | TN-21, TN-23 | Alta |
| 11 | Sem varredura de dependências, sem fixação de versão superior. | `requirements.txt` só com `>=`. | SG-14 | Baixa |
| 12 | A máquina de estados do job aceita qualquer transição. | `JobService._update`. | PD-05 | Baixa |

**Já está bem feito (manter):** o *subprocess* usa lista de argumentos, sem *shell*; o nome do arquivo é sanitizado; o erro
inesperado não vaza detalhe; o JS nunca monta HTML (verificado por teste); a saída da IA é validada contra esquema e contra o
texto; o servidor escuta só em `127.0.0.1`; não há CORS aberto; segredos ficam fora do repositório; a chave da API nunca vai
para o navegador.

## Ordem sugerida de correção

1. **Imediato, barato e sem arquitetura nova:** itens 3, 4 e 6 (limite de upload, timeout no FFmpeg, tirar dado pessoal dos
   logs) e 9 (cabeçalhos).
2. **Antes de qualquer exposição na internet:** itens 1, 2, 5 e 10 (identidade, autorização, cotas, consentimento). É a fase 1
   do [roteiro](README.md#roteiro-de-evolução).
3. **Junto com a fase 2:** itens 7, 8, 11 e 12.

## Verificação

- **Automática (já existe):** o JS não injeta HTML; o FFmpeg e o Gemini têm ponto único de contato; não há `print` fora da CLI
  (`tests/test_architecture.py`).
- **A criar:** varredura de isolamento entre tenants (ver [multi-tenancy](multitenancia.md#testes-obrigatórios-de-isolamento));
  teste que falha se um log de `lessons/` ou `diarization/review.py` carregar texto de fala; teste de limite de upload.
- **Periódica:** revisão de dependências, teste de restauração de *backup*, simulação de incidente.
