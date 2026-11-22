# ADR-0004: Arquivos no disco por tenant em vez de armazenamento de objetos

## Contexto

A regra TN-08 define que áudios, relatórios e materiais devem residir em armazenamento de objetos (como S3 ou Google Cloud Storage) com URLs assinadas de validade curta.
Em ambiente de desenvolvimento e testes locais, operar emuladores de S3 (como MinIO ou LocalStack) adiciona dependências pesadas e passos manuais de configuração.

## Decisão

Armazenar os arquivos de mídia e relatórios diretamente no sistema de arquivos local, organizados estritamente sob o diretório do tenant:
`output/tenants/<tenant_id>/sessions/<session_id>/`
(sempre restrito ao diretório `output/` conforme RN-29).
O acesso é intermediado por endpoints da API com verificação de `TenantContext`, garantindo que arquivos de um tenant nunca sejam servidos a outro.

## Consequências

- **Positivas:** Leitura e gravação diretas sem rede ou credenciais de nuvem; fácil depuração e limpeza local.
- **Negativas:** Armazenamento acoplado ao disco da máquina local; não escala horizontalmente com múltiplas instâncias da API.

## Alternativas descartadas

- **MinIO / LocalStack local:** Descartado para o MVP para evitar dependência de Docker.
- **Armazenamento plano sem separação de tenant:** Descartado para garantir conformidade imediata com a estrutura hierárquica por organização.

## Quando trocar

Trocar por armazenamento de objetos (compatível com S3) e URLs assinadas de curta duração na migração para produção na nuvem/VPS.
