# Multi-tenancy da Pauta

Este é o documento central para a fase 2. Uma falha aqui significa que a voz e os erros de alunos de uma escola aparecem
para outra. Por isso as regras são duras e quase todas têm um teste que as sustenta.

Veja também: [arquitetura](README.md) · [segurança](seguranca.md).

## Estado atual

Não há tenant, usuário nem autenticação. O servidor escuta em `127.0.0.1` e qualquer pessoa na máquina vê todas as aulas.
`JobService` guarda os jobs num dicionário, e o único segredo de acesso a uma aula é o ID de 12 caracteres hexadecimais
(48 bits). Isso é aceitável para uma ferramenta local e **inaceitável** para um serviço. Tudo abaixo é o alvo.

## O que é um tenant

**Tenant = a organização cliente**: uma escola, um curso, uma rede, ou um professor autônomo (que recebe um *workspace* de um
único usuário, para que o modelo seja o mesmo). Usuários pertencem a um ou mais tenants por *vínculo* com papel.

| Conceito | Descrição |
|---|---|
| Tenant | Organização. Dono dos dados, do plano e das cotas. |
| Usuário | Pessoa autenticada pelo provedor de identidade. Pode ter vínculo com mais de um tenant. |
| Vínculo (*membership*) | Usuário + tenant + papel: `owner` (cobrança, exclusão, convites), `teacher` (aulas e material próprios), `coordinator` (leitura das aulas do tenant, sem edição). |
| Aluno | Pessoa **do tenant**, não usuária do sistema. Entidade com dado pessoal, e por isso sujeita a retenção e exclusão. |
| Aula (`ClassSession`) | A gravação e seus resultados. Pertence a um tenant e a um professor. |

## Estratégia de isolamento

Há três modelos clássicos. A decisão:

| Modelo | Como é | Custo | Isolamento | Decisão |
|---|---|---|---|---|
| **Compartilhado com RLS** | Um banco, um esquema, `tenant_id` em toda tabela, e *Row Level Security* no Postgres | Baixo | Bom, se o RLS for a rede de segurança e não a única defesa | **Padrão** (fase 2) |
| Esquema por tenant | Um esquema por cliente no mesmo banco | Médio; migrações multiplicam | Melhor | Não adotar |
| Banco por tenant | Um banco por cliente | Alto | Máximo | **Opcional** (fase 3), para clientes que exigirem contrato |

Por quê: o público é de escolas pequenas e professores autônomos, muitos tenants com pouco volume. Banco por tenant seria um
custo operacional que o preço do produto não paga. O RLS entrega um segundo trinco: mesmo que o código esqueça um filtro, o
banco recusa.

Defesa em profundidade: **três camadas independentes** (aplicação, repositório e banco) precisam estar de acordo para um
dado sair. Nenhuma sozinha é suficiente.

## Regras

### Identidade e resolução do tenant

| Código | Regra |
|---|---|
| TN-01 | **DEVE** o tenant do chamador vir **somente** do token autenticado (e do vínculo ativo), nunca de parâmetro, corpo, cabeçalho ou subdomínio informado pelo cliente. Quando o usuário tem vários vínculos, ele escolhe o ativo e o servidor valida o vínculo. |
| TN-02 | **DEVE** a rota receber um `TenantContext` imutável (`tenant_id`, `user_id`, `role`) criado pelo *middleware* de autenticação e passado explicitamente pelos casos de uso. Evite estado implícito: `contextvars` só alimenta log e o `SET LOCAL` do banco. |
| TN-03 | **DEVE** todo acesso a dado exigir o tenant na assinatura: `repo.get(tenant_id, session_id)`, nunca `repo.get(session_id)`. Uma consulta sem tenant não deve compilar nem passar no teste de arquitetura. |
| TN-04 | **DEVE** recurso de outro tenant responder **404**, igual a um recurso inexistente, nunca 403. Isso impede enumerar o que existe em outro tenant. |
| TN-05 | **DEVE** todo identificador exposto ser opaco e de 128 bits (UUID v4 completo), não o prefixo de 48 bits de hoje, nem sequencial. O ID **não** é credencial: a autorização é feita à parte (TN-03). |

### Dados

| Código | Regra |
|---|---|
| TN-06 | **DEVE** toda tabela de dado de cliente ter `tenant_id NOT NULL`, chave estrangeira para `tenants`, e índice com `tenant_id` como primeira coluna. Chaves únicas incluem o tenant (`UNIQUE (tenant_id, ...)`). |
| TN-07 | **DEVE** o banco impor *Row Level Security* em toda tabela com `tenant_id`, e a aplicação **não** conectar como dono da tabela nem com `BYPASSRLS`. A cada transação a aplicação faz `SET LOCAL app.tenant_id = ...`. Tarefas administrativas usam outro papel, auditado. |
| TN-08 | **DEVE** arquivo (áudio, relatório, material) ficar em caminho com o tenant como prefixo (`tenants/<tenant_id>/sessions/<session_id>/...`), com acesso por URL assinada de validade curta (minutos), nunca por caminho informado pelo cliente. Criptografia em repouso ligada; um bucket por ambiente. |
| TN-09 | **DEVERIA** cada tenant ter configuração própria em tabela, não em código: nível padrão, idioma, nome e logotipo da folha, retenção. Funcionalidade por plano via *feature flag* lida do tenant. |
| TN-10 | **DEVE** migração de esquema ser em duas etapas (expandir e contrair) e compatível com a versão anterior da aplicação em execução, para permitir *deploy* sem parada. Nova coluna de tenant nasce nula, é preenchida em lote e só depois vira `NOT NULL`. |

Esboço do esquema (conceitual; os nomes finais saem do ADR):

```sql
CREATE TABLE tenants (id uuid PRIMARY KEY, name text NOT NULL, plan text NOT NULL, retention_days int NOT NULL);
CREATE TABLE memberships (tenant_id uuid REFERENCES tenants, user_id uuid, role text NOT NULL,
                          PRIMARY KEY (tenant_id, user_id));
CREATE TABLE students (id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants, display_name text NOT NULL,
                       deleted_at timestamptz);
CREATE TABLE class_sessions (id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants, teacher_id uuid NOT NULL,
                             status text NOT NULL, created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL);
CREATE TABLE usage_events (id bigserial PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants,
                           session_id uuid, kind text NOT NULL, audio_seconds numeric, tokens int, at timestamptz NOT NULL);
CREATE TABLE audit_log (id bigserial PRIMARY KEY, tenant_id uuid NOT NULL, actor_id uuid NOT NULL,
                        action text NOT NULL, target text, at timestamptz NOT NULL, request_id text);

ALTER TABLE class_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE class_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON class_sessions
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

### Processamento assíncrono

| Código | Regra |
|---|---|
| TN-11 | **DEVE** toda mensagem de fila carregar `tenant_id` e `session_id`. O *worker* reconstrói o `TenantContext` a partir da mensagem, revalida que a aula pertence ao tenant e só então processa. Nada de "ID global de job". |
| TN-12 | **DEVE** haver **justiça entre tenants** (*noisy neighbor*): limite de jobs simultâneos por tenant (hoje o limite é global, `MAX_CONCURRENT_JOBS = 2`), e fila que alterna entre tenants em vez de ser um único bloco FIFO. Um tenant que envia 50 aulas não atrasa os demais. |
| TN-13 | **DEVE** o *worker* não manter dado de um tenant entre jobs: sem cache global de transcrição, sem arquivo temporário compartilhado. Diretório de trabalho por job, apagado ao final. |

### Cotas, uso e custo

Cada aula chama uma API paga. Sem controle, um tenant (ou um atacante com uma conta) gera custo ilimitado (*denial of wallet*).

| Código | Regra |
|---|---|
| TN-14 | **DEVE** haver medição de uso por tenant: minutos de áudio transcritos e tokens consumidos, gravados em `usage_events` por quem chama o Gemini (o decorator do PD-08). O custo é atribuído ao tenant, não à plataforma. |
| TN-15 | **DEVE** a cota do plano ser verificada **antes** da chamada paga (pré-checagem pela duração do áudio) e **também** depois, com o consumo real. Estouro devolve `429` com mensagem que diz o limite e quando renova. |
| TN-16 | **DEVERIA** haver limite de taxa por usuário e por tenant (SG-08) e teto de despesa diário por tenant, com alerta à plataforma ao passar de 80%. |
| TN-17 | **PODE** o tenant levar a própria chave do Gemini (BYOK), guardada com criptografia por envelope e chave de criptografia por tenant. Quem leva a chave assume a cota do fornecedor. |

### Dados pessoais e ciclo de vida (LGPD)

Voz, nome e erros de fala de alunos, que podem ser menores de idade, são dados pessoais. O tenant é o **controlador**; a
Pauta é a **operadora**.

| Código | Regra |
|---|---|
| TN-18 | **DEVE** haver **minimização**: guardar o áudio só pelo tempo necessário. Por padrão, o áudio é apagado após a transcrição e o material é mantido por `retention_days` do tenant. O padrão é decidido com o jurídico. |
| TN-19 | **DEVE** haver exclusão sob demanda em três escopos, com rastro de auditoria: uma aula, um aluno (inclusive as falas dele nas aulas), um tenant inteiro (offboarding). A exclusão atinge banco, arquivos, fila e *backups* dentro do prazo declarado. |
| TN-20 | **DEVE** haver exportação dos dados de um tenant em formato aberto (JSON e arquivos). |
| TN-21 | **DEVE** o aceite de consentimento (do responsável, no caso de menores) ser registrado pelo professor antes do envio, com data, versão do texto e quem aceitou. Sem aceite, o envio é bloqueado. (Decisão em aberto em [regras de negócio](../produto/regras-de-negocio.md), RN-28.) |
| TN-22 | **DEVE** o texto de fala nunca aparecer em log, métrica, rastreio ou mensagem de erro. Somente identificadores. |
| TN-23 | **DEVE** ficar claro, antes de ativar, o que o provedor de IA faz com os dados (retenção, uso para treinamento, país de processamento). **Ponto a validar com o jurídico, contra os termos do plano contratado**; até lá, o produto não faz promessa de privacidade maior do que a verificada. |

### Observabilidade e suporte

| Código | Regra |
|---|---|
| TN-24 | **DEVE** todo log, rastreio e métrica ter `tenant_id` como campo, para isolar incidente de um cliente sem abrir dado de outro. |
| TN-25 | **DEVE** o acesso de suporte a dado de cliente ser excepcional: exige justificativa, tem prazo curto, é auditado e visível ao tenant. Ninguém da plataforma lê aulas "por curiosidade". |

## Testes obrigatórios de isolamento

Sem estes testes, nenhuma regra acima vale:

1. **Varredura de rotas.** Um teste percorre todas as rotas que recebem um identificador, cria o recurso como tenant A e tenta
   ler, alterar, baixar e excluir como tenant B. Esperado: sempre 404. Uma rota nova entra na varredura automaticamente; rota
   fora da lista falha o teste.
2. **Repositório.** Para cada método, chamar com o tenant errado devolve vazio.
3. **RLS.** Com a conexão da aplicação e `app.tenant_id` de A, uma consulta crua (`SELECT * FROM class_sessions`) só devolve
   linhas de A. Com `app.tenant_id` vazio, não devolve nada.
4. **Fila.** Uma mensagem com `tenant_id` trocado é recusada pelo *worker*.
5. **Arquivos.** URL assinada de um tenant não abre arquivo de outro, e expira.
6. **Justiça.** Um tenant com muitas aulas na fila não impede o início das aulas de outro dentro de um prazo.
7. **Exclusão.** Excluir um aluno remove as falas dele de banco e arquivos, e o resto da aula continua íntegro.

## Caminho de migração a partir do código de hoje

| Passo | Mudança | Onde |
|---|---|---|
| 1 | Introduzir `TenantContext`, `TenantId`, `SessionId` e o `SessionRepository` (porta), com implementação em memória que já exige o tenant. | `application/`, `web/jobs.py` |
| 2 | Trocar o ID de 48 bits por UUID completo. | `JobService.submit` |
| 3 | `JobService.list` e `get` passam a receber o tenant. Autenticação provisória com um único usuário/tenant fixo, para a suíte de isolamento já existir. | `web/` |
| 4 | Persistência em banco, com RLS; armazenamento de objetos atrás de `BlobStore`. | novo adaptador |
| 5 | Fila e *worker* separados; limite por tenant. | `cli/` (novo ponto de entrada) |
| 6 | Medição de uso, cotas e auditoria. | decorator em `asr/gemini.py` |
| 7 | Exclusão, exportação e retenção. | `application/` |

O passo 1 a 3 já pode acontecer na fase 1 e deixa o código pronto para o resto sem mudar nenhuma regra de negócio.
