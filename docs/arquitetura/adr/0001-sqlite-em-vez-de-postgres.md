# ADR-0001: SQLite (sqlite3 da stdlib) em vez de Postgres

## Contexto

A Pauta está evoluindo de uma ferramenta local monousuário para um serviço multi-tenant inicial (MVP) operando em localhost.
A regra padrão do projeto para produção com múltiplos tenants é Postgres compartilhado com Row Level Security (RLS) (TN-06, TN-07).
No entanto, na fase de MVP em localhost, operar um servidor Postgres exigiria containers (Docker), processos externos ou gerenciamento de infraestrutura, aumentando a fricção de desenvolvimento e testes.

## Decisão

Adotar o `sqlite3` da biblioteca padrão do Python, gravando em um arquivo único local (`output/pauta.db`).
Como o SQLite não possui Row Level Security (RLS) nativo:
1. O isolamento entre tenants é garantido estritamente na aplicação e no repositório: toda consulta exige `tenant_id` (`repo.get(tenant_id, session_id)`).
2. O isolamento é auditado e travado por uma suíte de testes de varredura que testa todas as rotas da aplicação como Tenant B tentando acessar dados do Tenant A.

## Consequências

- **Positivas:** Zero dependências externas; sem necessidade de Docker ou serviços rodando em background; execução de testes extremamente rápida; portabilidade instantânea.
- **Negativas:** Ausência da segunda camada de trava de segurança no banco (RLS); controle de concorrência limitado a gravações em fila única (WAL mode).

## Alternativas descartadas

- **Postgres local com Docker:** Descartado para o MVP para manter a execução com um único comando sem dependências do sistema operacional.
- **Dicionário em memória:** Descartado porque os dados de aulas sumiam ao reiniciar o servidor.

## Quando trocar

Trocar por Postgres com Row Level Security (RLS) quando o serviço for implantado em produção com mais de um servidor web ou quando atingir cerca de 50 escolas cadastradas.
