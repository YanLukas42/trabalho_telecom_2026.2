# Regras de negócio da Pauta

Cada regra tem um código (`RN-xx`) para ser citada em histórias, testes e código. A coluna **Onde** aponta para o ponto do
código que a faz valer, e **Situação** diz se ela já é aplicada pelo sistema:

- `aplicada`: o código garante a regra.
- `parcial`: o código garante uma parte; o que falta está descrito.
- `pretendida`: é uma decisão de produto que ainda não tem código por trás.

As histórias que dependem de cada regra estão em [historias-de-usuario.md](historias-de-usuario.md).

## Entrada e fila

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-01 | Só se aceitam arquivos `.mp4 .mp3 .wav .m4a .aac .ogg .flac .mkv .webm`. Outro formato é recusado antes de salvar, com a lista de formatos aceitos. | `settings.MEDIA_EXTENSIONS`, `JobService.submit` | aplicada |
| RN-02 | Arquivo vazio é recusado e nada fica gravado no disco. O nome do arquivo é limpo: só o nome-base, sem caminho nem caracteres especiais. | `JobService.submit`, `sanitize_filename` | aplicada |
| RN-03 | O áudio enviado ao Gemini tem teto de 20 MB (limite da API para dados inline). Com Opus 16 kbps, cabem cerca de 2 h 50 min; a gravação é validada contra o teto de 3 h antes do processamento (`ffprobe`). | `GeminiDiarizer`, `JobService.submit`, `audio/ffmpeg.py` | aplicada |
| RN-04 | O envio aceita no máximo 300 MB (contados em streaming durante a leitura) e áudio com duração máxima de 3 horas (`ffprobe`). Arquivos acima do limite são recusados cedo no cliente (`upload.js`) e no servidor (`create_session`), e os arquivos parciais são apagados. | `js/views/upload.js`, `JobService.submit`, `create_session` | aplicada |
| RN-05 | No máximo 2 aulas são processadas ao mesmo tempo e há limite de concorrência de 1 aula ativa por professor e 2 ativas por escola (`429`). As demais aguardam na fila quando aplicável. | `MAX_CONCURRENT_JOBS`, `SessionRepository.count_active`, `JobService.submit` | aplicada |
| RN-06 | Uma aula tem quatro estados: na fila, processando, pronta e falhou. Falha conhecida mostra o motivo ao professor. Falha inesperada mostra uma mensagem genérica e o detalhe vai só para o log. | `JobStatus`, `JobService._run` | aplicada |
| RN-07 | Resposta inválida do Gemini (JSON ilegível ou fora do esquema) falha a aula. Nunca se grava relatório vazio. | `GeminiDiarizer`, `parse_chunk_json` | aplicada |

## Transcrição e participantes

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-08 | Há dois motores. O padrão é o Gemini (nuvem, o áudio inteiro numa chamada, sem fatiar). O local usa pyannote para os turnos e Whisper para as palavras, e só fica disponível com `HF_TOKEN` e as dependências locais instaladas. Um motor indisponível aparece desabilitado com o motivo. | `diarization/factory.py` | aplicada |
| RN-09 | A IA só atribui um nome a uma voz se o próprio texto trouxer a pista (apresentação ou vocativo), com confiança mínima de 0,7 e com o trecho de evidência presente literalmente na transcrição. Sem isso, o nome fica em branco. A revisão nunca altera o texto original. | `review.identified_names` | aplicada |
| RN-10 | Na tela "Quem é quem", a sugestão inicial de professor é quem tem "prof", "teacher" ou "tutor" no nome; se ninguém tiver, quem mais fala. O professor pode trocar. Todo participante é professor ou aluno. | `js/views/session.js` | aplicada |
| RN-11 | Os papéis e os nomes escolhidos ficam salvos no servidor por aula (`participants_json`) via `PUT /api/v1/sessions/{id}/participants` e aparecem em qualquer computador. | `js/views/session.js`, `update_participants`, `SessionRepository` | aplicada |
| RN-12 | Para o idioma de aula, o prompt do Gemini manda transcrever sem corrigir erros do aluno e manter inglês em inglês e português em português. O Whisper local transcreve em inglês. | `build_class_prompt`, `serve.CLASS_LANGUAGE` | aplicada |

## Material de aula

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-13 | O nível da turma é um destes: A1, A2, B1, B2, C1, C2. A tela sugere B1. | `LEVELS` | aplicada |
| RN-14 | O professor pede de 3 a 10 atividades por aluno. A sugestão é 6. Se a IA devolver mais, o excedente é cortado. | `MIN_EXERCISES`, `MAX_EXERCISES`, `validated_materials` | aplicada |
| RN-15 | O foco da próxima aula é opcional e tem até 300 caracteres. | `MAX_FOCUS_CHARS` | aplicada |
| RN-16 | Um erro só entra na folha de um aluno se a citação existir literalmente nas falas **dele** (sem diferenciar maiúsculas e pontuação). Citação inventada ou de outro aluno é descartada. | `validated_materials` | aplicada |
| RN-17 | Só quem foi marcado como aluno recebe folha. Folha para professor ou para voz desconhecida é descartada. É obrigatório marcar ao menos um aluno. | `LessonRequest`, `validated_materials` | aplicada |
| RN-18 | Se nenhuma folha válida sobrar, o pedido falha com mensagem para tentar de novo. Nunca se mostra material vazio. | `validated_materials` | aplicada |
| RN-19 | Cada folha tem: um ponto forte, os erros reais da aula (pode ser nenhum) e as atividades. As atividades podem ser de quatro tipos: lacuna, múltipla escolha, reescrever e resposta curta, cada uma com resposta. O plano tem objetivo, tópicos, etapas com minutos e tarefa de casa. | `LessonMaterials` | aplicada |
| RN-20 | Gerar de novo ou editar o material substitui o material anterior da aula no SQLite (`class_sessions.lesson_json`). | `JobService.attach_lesson`, `update_lesson`, `SessionRepository` | aplicada |
| RN-21 | Criar material exige o Gemini configurado, inclusive quando a transcrição foi feita no motor local: o texto (não o áudio) é enviado ao Gemini. | `create_lesson` | aplicada |
| RN-22 | A IA trabalha só com o texto e não ouve o áudio. A interface sempre avisa o professor para conferir o material antes de entregar, porque uma palavra mal transcrita pode virar "erro" do aluno. | texto na tela "Atividades" (`js/views/sheets.js`) | aplicada |
| RN-23 | Falas do aluno em português não são erro. Trechos que pareçam erro de reconhecimento, e não de inglês, devem ser ignorados. Aluno que falou pouco recebe atividades sobre o tema da aula e nenhum erro. | prompt de `build_lesson_prompt` | parcial: o prompt pede, o código não consegue verificar |

## Impressão e entrega

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-24 | A folha impressa para o aluno nunca traz as respostas. O gabarito é um documento separado, para o professor. | `js/views/sheets.js`, CSS `@media print` | aplicada |
| RN-25 | O PDF sai do imprimir do navegador, em preto e branco, uma folha por página. Não há biblioteca de PDF nem arquivo gerado no servidor. | `js/print.js`, CSS `@media print` | aplicada |

## Dados, privacidade e custo

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-26 | As aulas e materiais vivem no SQLite (`output/pauta.db`) e os arquivos ficam em `output/tenants/<tenant_id>/sessions/<session_id>/`. Ao reiniciar o servidor, aulas que estavam na fila ou processando passam para `falhou` ("servidor reiniciou, envie de novo"). | `storage/db.py`, `SessionRepository`, `JobService` | aplicada |
| RN-27 | A tela de envio informa explicitamente ao professor: "O áudio e o texto da aula são processados pelo Google Gemini." | `js/views/upload.js`, `create_session` | aplicada |
| RN-28 | O envio exige o aceite explícito do professor ("Tenho autorização dos alunos (ou dos responsáveis) para gravar e processar esta aula." e `consent=true`), registrando `consent_at` e `consent_version` no banco. | `js/views/upload.js`, `create_session`, `JobService.submit` | aplicada |
| RN-29 | Nada é gravado fora de `output/`. O áudio intermediário em `output/diarizacao/audio/` e arquivos por tenant ficam restritos a `output/`. | `.gitignore`, `settings` | aplicada |
| RN-30 | O custo de API é estimado por tokens (US$ 0,15 por milhão na entrada e US$ 0,60 na saída, câmbio de referência 5,70) e continua no relatório técnico. A interface da Pauta não mostra custo ao professor. | `metrics/cost.py`, `settings` | aplicada |

## Contas, cotas, auditoria e edição

| Código | Regra | Onde | Situação |
|---|---|---|---|
| RN-33 | Acesso por senha (`scrypt`, mínimo 10 caracteres, criação via `telecom.cli.admin`), sessão de 12 h em cookie `pauta_session` (`HttpOnly`, `SameSite=Strict`, `Secure` via `PAUTA_COOKIE_SECURE`), limite de 5 erros em 15 min (`429`), checagem CSRF por `Origin` e isolamento multi-tenant (`teacher` vê só suas aulas; `owner` vê todas da escola; outro tenant ou outro professor recebe sempre `404`). | `accounts/passwords.py`, `web/auth.py`, `storage/repositories.py`, `tests/test_isolation.py` | aplicada |
| RN-34 | Cada escola tem cota mensal (`monthly_audio_minutes`) verificada antes do envio (`429` com data de renovação), com registro em `usage_events` após transcrição e geração de material. | `JobService.submit`, `UsageRepository`, `create_lesson` | aplicada |
| RN-35 | Excluir uma aula exige confirmação na tela e apaga a linha no banco, a pasta em `output/tenants/<tenant_id>/sessions/<session_id>/` e registra evento em `audit_log` (LGPD). | `delete_session`, `AuditRepository`, `js/views/sessions.js`, `js/views/session.js` | aplicada |
| RN-36 | O professor pode editar o material antes de imprimir (enunciado, opções, resposta esperada, remoção de erro e de atividade), validado contra `LessonMaterials` via `PUT /api/v1/sessions/{id}/lesson`. | `update_lesson`, `js/views/sheets.js` | aplicada |

## Mensagens

| Código | Regra | Situação |
|---|---|---|
| RN-31 | Todo texto para o professor é em português do Brasil, com os nomes fixos do guia de voz: aula, aluno, atividades, folha, gabarito, plano da próxima aula. Os enunciados e respostas das atividades são em inglês. Veja [a identidade visual](../identidade-visual/README.md). | aplicada |
| RN-32 | Mensagem de erro diz o que aconteceu e o que fazer. Não pede desculpas e não mostra detalhes técnicos. | aplicada |

## Decisões em aberto

Pontos que o produto ainda precisa decidir para as fases seguintes:

1. **Retenção automática.** O professor já pode excluir manualmente uma aula e seus arquivos (RN-35); falta definir o prazo automático de expiração e purga de gravações antigas.
2. **Aula individual.** Com um único aluno, o professor e o aluno às vezes se confundem na diarização. É preciso um caminho para corrigir falas atribuídas à pessoa errada.
3. **Outros idiomas.** O prompt, os níveis (CEFR) e a identidade assumem inglês. Espanhol ou francês exigem revisão.
4. **Planos pagos e cobrança externa.** A cota mensal por escola (RN-34) já funciona no MVP local; integração com cobrança/faturamento fica para depois do MVP.
