# Ordem dos PRs — MVP Multi-Tenant da Pauta

Este roteiro organiza a entrega do MVP multi-tenant em **6 PRs pequenos e incrementais**, conforme a ordem do item 12. Cada PR registra as regras de negócio (`RN`) e histórias (`US`) atualizadas e declara explicitamente se houve mudança no contrato da API HTTP.

> Antes de abrir ou fazer merge de qualquer PR, execute `python -m pytest` na raiz do repositório e confirme que toda a suíte passa (sem chamar a API real do Gemini).

---

## PR 1 — Segurança rápida + ID UUID completo

- **Objetivo:** Corrigir as lacunas imediatas de segurança sem alterar o fluxo funcional nem introduzir banco de dados ou contas.
- **Mudanças principais:**
  - Remover dados pessoais (fala do aluno, nomes sugeridos, nomes de arquivos enviados e detalhes de erro) dos logs em `telecom/lessons/materials.py`, `telecom/diarization/review.py`, `telecom/diarization/pipeline.py` e `telecom/web/jobs.py`.
  - Adicionar `timeout` em `subprocess.run` (`FFMPEG_TIMEOUT_SEC = 900`, `FFPROBE_TIMEOUT_SEC = 60`) e `-protocol_whitelist file,pipe` (e `file` no `ffprobe`) em `telecom/audio/ffmpeg.py`.
  - Adicionar `SecurityHeadersMiddleware` em `telecom/web/app.py` com `Content-Security-Policy` (`default-src 'self'; media-src 'self'; img-src 'self' data:; frame-ancestors 'none'`), `X-Content-Type-Options: nosniff` e `Referrer-Policy: no-referrer`.
  - Hospedar fontes locais (`.woff2` + `fonts.css`) em `telecom/web/static/fonts/` e remover links externos do Google Fonts em `telecom/web/static/index.html`.
  - Expandir identificadores de sessão para UUID v4 completo de 128 bits (`uuid4().hex`).
  - Testes em `tests/test_security_audit.py`.
- **Regras e histórias impactadas:** Atende diretamente às regras de segurança (`SG-07`, `SG-10`, `SG-11`) e `TN-05` (`docs/arquitetura/seguranca.md`).
- **Mudança de contrato da API:** **Sim (menor)**. O campo `id` retornado nas respostas de sessão/job passa de 12 caracteres hexadecimais para UUID hexadecimal completo de 32 caracteres (formato opaco). Rotas e verbos permanecem inalterados.

---

## PR 2 — `storage/` + SQLite + `JobService` com repositório + recuperação no reinício

- **Objetivo:** Substituir o dicionário em memória por persistência durável em SQLite sem dependências novas, preservando compatibilidade inicial com 1 usuário/tenant padrão.
- **Mudanças principais:**
  - Criar `telecom/storage/db.py` (ponto único de contato de `sqlite3`, modo WAL, `PRAGMA foreign_keys=ON`, tabela `schema_version` + migrações SQL em ordem e `.backup()`) e `telecom/storage/repositories.py` (`SessionRepository`, `UserRepository`, `AuthSessionRepository`, `LoginAttemptRepository`, `UsageRepository`, `AuditRepository`) com `tenant_id` obrigatório como primeiro parâmetro.
  - Criar schema para `tenants`, `users`, `auth_sessions`, `class_sessions`, `usage_events`, `audit_log` e `login_attempts` (todos os índices iniciando em `tenant_id`).
  - Armazenar arquivos por tenant em `output/tenants/<tenant_id>/sessions/<session_id>/` (ADR-0004).
  - Atualizar `JobService` (`telecom/web/jobs.py`) para usar `SessionRepository` e marcar sessões em `queued` ou `processing` como `failed` ("servidor reiniciou, envie de novo") na inicialização (ADR-0003).
  - Registrar regra de arquitetura em `tests/test_architecture.py` (`LAYER["storage"] = 4`, `SINGLE_CONTACT["sqlite3"] = "telecom/storage/db.py"`) e testes em `tests/test_storage.py` e `tests/test_web_jobs.py`.
- **Regras e histórias impactadas:** `RN-26` (`aplicada`), base para `US-14`.
- **Mudança de contrato da API:** **Não**.

---

## PR 3 — `accounts/` + login + CLI de admin + `Principal` em todas as rotas + `/api/v1` + `test_isolation`

- **Objetivo:** Introduzir isolamento multi-tenant de ponta a ponta com autenticação por cookie de sessão e versionamento da API em `/api/v1`.
- **Mudanças principais:**
  - Criar pacote puro `telecom/accounts/` (`models.py` com `Tenant`, `User`, `Principal` imutáveis; `passwords.py` com `hashlib.scrypt`, salt de 16 bytes, mínimo 10 caracteres e `hmac.compare_digest`; `LAYER["accounts"] = 1`).
  - Criar `telecom/cli/admin.py` (`create-tenant`, `create-user`, `reset-password` via `getpass`).
  - Criar `telecom/web/auth.py` com `AuthManager` (cookie `pauta_session` `HttpOnly`/`SameSite=Strict`/`Secure` condicional em `PAUTA_COOKIE_SECURE=1`, validade 12 h, rate limit 5 falhas/15 min $\to$ `429`, erro genérico `401`), `verify_csrf` (checagem de `Origin` em `POST`/`PUT`/`DELETE`) e dependência `current_principal`.
  - Migrar as rotas para `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/me`, `/api/v1/config` e `/api/v1/sessions/*` exigindo `Principal`, removendo as rotas sem versão `/api/*` e respondendo sempre `404` (nunca `403`) para recursos de outra escola ou de outro professor.
  - Cobrir com `tests/test_accounts.py`, `tests/test_auth.py`, `tests/test_web_auth.py`, `tests/test_cli_admin.py` e varredura dinâmica de `app.routes` em `tests/test_isolation.py`.
- **Regras e histórias impactadas:** `RN-33` (nova, `aplicada`), `US-17` (`feito`).
- **Mudança de contrato da API:** **Sim (quebra de versão / v1)**. As rotas antigas `/api/config` e `/api/jobs/*` são removidas e substituídas pelo prefixo `/api/v1/*` (`/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/me`, `/api/v1/config`, `/api/v1/sessions/*`), todas exigindo autenticação via cookie `pauta_session` (exceto login/logout). `JobView` passa a expor `audio_seconds` e `has_lesson`.

---

## PR 4 — Cotas, limites, `usage_events`, auditoria e `DELETE`

- **Objetivo:** Impor proteções contra abuso de custo/disco e atender aos direitos de exclusão (LGPD) com rastreabilidade.
- **Mudanças principais:**
  - Aplicar limite de upload de 300 MB contado em streaming em `JobService.submit` (`413`), abortando e limpando arquivos parciais imediatamente.
  - Verificar duração via `ffprobe` logo após salvar, rejeitando áudios acima de 3 horas (`400`) antes do processamento.
  - Verificar cota mensal por escola (`monthly_audio_minutes`) com retorno `429` informando uso e data de renovação.
  - Limitar concorrência a 1 aula ativa por professor e 2 por escola (`429`).
  - Gravar `usage_events` após transcrição e geração de material (com `audio_seconds` e `tokens`).
  - Implementar `DELETE /api/v1/sessions/{session_id}` removendo linha do SQLite, apagando diretório do disco e registrando ação em `audit_log`.
  - Cobrir com `tests/test_quota.py`, `tests/test_quotas_and_limits.py` e `tests/test_upload_limits.py`.
- **Regras e histórias impactadas:** `RN-03`, `RN-04`, `RN-05`, `RN-34` (nova), `RN-35` (nova) $\to$ todas `aplicada`; `US-14` (`feito`), `US-18` (atualizada com recusa antecipada).
- **Mudança de contrato da API:** **Sim**. `POST /api/v1/sessions` passa a retornar códigos `413` (> 300 MB), `400` (> 3 h) e `429` (cota mensal ou concorrência excedida); nova operação `DELETE /api/v1/sessions/{session_id}` retorna `200` com confirmação de exclusão LGPD.

---

## PR 5 — Front-end: divisão do `app.js`, novas rotas, login, Minhas aulas e consentimento

- **Objetivo:** Eliminar o arquivo monolítico `app.js`, adotar módulos ES nativos sem build e adaptar a interface ao fluxo multi-tenant e LGPD.
- **Mudanças principais:**
  - Substituir `telecom/web/static/app.js` por módulos ES em `telecom/web/static/js/` (`dom.js`, `api.js`, `format.js`, `router.js`, `print.js`, `main.js` e `views/{login,sessions,upload,session,sheets,plan}.js`), todos com $\le 400$ linhas e sem `innerHTML`.
  - Atualizar `telecom/web/static/index.html` com `<script type="module" src="/js/main.js">`, nova barra superior (`Pauta | Minhas aulas | Nova aula | nome da escola | Sair`) e remoção da barra lateral.
  - Implementar rotas `#/entrar`, `#/` (Minhas aulas com cota do mês no topo, selo *"Material pronto"* e exclusão com confirmação) e `#/nova` (validação precoce de 300 MB/extensão, aviso explícito do Google Gemini e checkbox obrigatório de consentimento enviando `consent=true`).
  - Atualizar `tests/test_architecture.py` (remover exceção de `app.js`, validar `static/js/**/*.js`) e criar `tests/test_ux_and_modules.py`.
- **Regras e histórias impactadas:** `RN-04`, `RN-24`, `RN-25`, `RN-27`, `RN-28` (`aplicada`); `US-14`, `US-17` (`feito`).
- **Mudança de contrato da API:** **Sim (campo obrigatório no upload)**. `POST /api/v1/sessions` passa a exigir o campo de formulário `consent=true` (rejeitando com `400` se ausente ou falso) e persiste `consent_at` e `consent_version`.

---

## PR 6 — Editar material + participantes no servidor

- **Objetivo:** Persistir papéis/nomes no servidor (saindo do `localStorage`) e permitir que o professor edite enunciados, opções, respostas e erros antes de imprimir.
- **Mudanças principais:**
  - Implementar e integrar `PUT /api/v1/sessions/{session_id}/participants` em `telecom/web/static/js/views/session.js`, removendo completamente o `localStorage`.
  - Implementar e integrar `PUT /api/v1/sessions/{session_id}/lesson` em `telecom/web/static/js/views/sheets.js` (modo editar na folha, campos de enunciado/opções/resposta, remover erro, remover/adicionar atividade), validado pelo schema `LessonMaterials`.
  - Cobrir com `tests/test_api_v1_sessions.py`, `tests/test_isolation.py` e `tests/test_ux_and_modules.py`.
- **Regras e histórias impactadas:** `RN-10`, `RN-11`, `RN-20`, `RN-36` (nova) $\to$ todas `aplicada`; `US-05` (atualizada com salvamento no servidor), `US-13` (`feito`).
- **Mudança de contrato da API:** **Sim (novas rotas de edição)**. Adição de `PUT /api/v1/sessions/{session_id}/participants` (recebe lista `ParticipantBody`) e `PUT /api/v1/sessions/{session_id}/lesson` (recebe payload `LessonMaterials`).
