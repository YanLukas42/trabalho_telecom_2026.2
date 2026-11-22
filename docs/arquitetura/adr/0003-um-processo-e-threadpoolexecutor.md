# ADR-0003: Um processo único (Uvicorn) e ThreadPoolExecutor

## Contexto

A regra AR-06 orienta que o trabalho pesado de áudio e IA deve rodar fora do processo da API web quando houver múltiplos usuários simultâneos.
No entanto, implantar um worker assíncrono separado com fila externa (Redis, Celery, RabbitMQ) para o MVP local aumentaria a infraestrutura e a complexidade operacional antes do necessário.

## Decisão

Executar a aplicação em um processo único com Uvicorn (1 worker) e utilizar o executor em pool de threads embutido (`ThreadPoolExecutor`), que já está presente no `JobService`.
Caso o servidor seja reiniciado enquanto houver aulas com status "na fila" ou "processando", a aplicação detecta esse estado durante a inicialização e marca a aula como `failed`, com a mensagem legível: "servidor reiniciou, envie de novo" (RN-06).

## Consequências

- **Positivas:** Inicialização simples com um único comando (`python -m telecom.cli.serve`); sem necessidade de broker de mensagens externo.
- **Negativas:** Se o processo da API cair, tarefas em execução são interrompidas; concorrência limitada a tarefas CPU/IO dentro do processo Python.

## Alternativas descartadas

- **Redis + Celery / RQ:** Descartado para o MVP para evitar daemons e containers locais.
- **Processos múltiplos com IPC:** Descartado por complexidade desnecessária em ambiente localhost.

## Quando trocar

Trocar por fila e worker dedicados separados quando o monólito de 1 processo não der conta da carga ou ao preparar o deploy em produção.
