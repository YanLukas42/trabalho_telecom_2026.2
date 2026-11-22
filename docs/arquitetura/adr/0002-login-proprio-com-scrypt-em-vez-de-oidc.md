# ADR-0002: Login próprio com scrypt em vez de OIDC

## Contexto

A regra SG-01 define que a autenticação em produção DEVE ser delegada a um provedor OIDC externo (Google, Microsoft, etc.) e que a Pauta não deve gerenciar credenciais de usuários.
Para o MVP em localhost, integrar um provedor OIDC introduz dependência de conexão com a internet, configuração de chaves de aplicativo, callbacks de domínio e complexidade de setup local.

## Decisão

Implementar autenticação própria local com e-mail e senha utilizando funções nativas da biblioteca padrão (`hashlib.scrypt` com salt criptográfico e comparação segura via `hmac.compare_digest`).
As contas de professores e escolas são criadas via CLI de administração (`cli/admin.py`) ou por migração de seed de desenvolvimento.
Não há cadastro aberto (signup público) nem fluxo de recuperação de senha por e-mail no MVP.
A sessão é mantida por cookie de sessão assinado (`HttpOnly`, `SameSite=Lax`). Esta decisão é uma exceção temporária registrada à regra SG-01.

## Consequências

- **Positivas:** Funciona offline e em localhost; zero bibliotecas externas adicionadas (sem passlib/bcrypt); fluxo direto e testável em milissegundos.
- **Negativas:** A Pauta armazena hashes de senhas locais; sem suporte a 2FA no MVP; exige criação prévia de contas por administrador.

## Alternativas descartadas

- **Integração OIDC completa:** Descartada temporariamente devido à dependência de rede e credenciais de provedores para testes locais.
- **Tokens JWT:** Descartado; cookies de sessão baseados em banco/memória local são mais simples e fáceis de invalidar no logout.

## Quando trocar

Trocar por OIDC quando o serviço for aberto para cadastro público na internet ou na ida para a VPS de produção.
