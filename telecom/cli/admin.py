"""CLI de administração para gerenciamento de tenants e usuários no SQLite.

Uso:
    python -m telecom.cli.admin create-tenant "Escola X" --minutes 600
    python -m telecom.cli.admin create-user --tenant <id> --email a@b.com --name "Ana" --role owner
    python -m telecom.cli.admin reset-password --email a@b.com

# shortcut: CLI local com getpass, trocar por painel web administrativo ou SSO na VPS (ADR-0002)
"""

import argparse
import getpass
import sys
import uuid
from pathlib import Path

from telecom.accounts.models import Tenant, User
from telecom.accounts.passwords import MIN_PASSWORD_LENGTH, hash_password
from telecom.settings import DATABASE_PATH
from telecom.storage.db import Database
from telecom.storage.repositories import UserRepository


def _get_user_repo(db_path: Path | str | None = None) -> UserRepository:
    path = db_path or DATABASE_PATH
    db = Database(path)
    return UserRepository(db)


def handle_create_tenant(args: argparse.Namespace, repo: UserRepository | None = None) -> int:
    user_repo = repo or _get_user_repo()
    tenant_id = getattr(args, "id", None) or uuid.uuid4().hex[:12]
    tenant = Tenant(
        id=tenant_id,
        name=args.name.strip(),
        monthly_audio_minutes=args.minutes,
    )
    user_repo.save_tenant(tenant)
    print(f"Tenant criado com sucesso:\n  ID: {tenant.id}\n  Nome: {tenant.name}\n  Minutos/mês: {tenant.monthly_audio_minutes}")
    return 0


def handle_create_user(args: argparse.Namespace, repo: UserRepository | None = None) -> int:
    user_repo = repo or _get_user_repo()
    tenant = user_repo.get_tenant(args.tenant)
    if not tenant:
        print(f"Erro: Tenant com ID '{args.tenant}' não encontrado.", file=sys.stderr)
        return 1

    email = args.email.lower().strip()
    if user_repo.get_user_by_email(email):
        print(f"Erro: Usuário com e-mail '{email}' já existe.", file=sys.stderr)
        return 1

    password = getattr(args, "password", None)
    if not password:
        password = getpass.getpass("Digite a senha (mínimo 10 caracteres): ")
        confirmation = getpass.getpass("Confirme a senha: ")
        if password != confirmation:
            print("Erro: As senhas não conferem.", file=sys.stderr)
            return 1

    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Erro: A senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.", file=sys.stderr)
        return 1

    pwd_hash = hash_password(password)
    user = User(
        id=uuid.uuid4().hex,
        tenant_id=args.tenant,
        email=email,
        name=args.name.strip(),
        password_hash=pwd_hash,
        role=args.role,
    )
    user_repo.save_user(user)
    print(f"Usuário criado com sucesso:\n  ID: {user.id}\n  Tenant: {user.tenant_id}\n  E-mail: {user.email}\n  Nome: {user.name}\n  Papel: {user.role}")
    return 0


def handle_reset_password(args: argparse.Namespace, repo: UserRepository | None = None) -> int:
    user_repo = repo or _get_user_repo()
    email = args.email.lower().strip()
    user = user_repo.get_user_by_email(email)
    if not user:
        print(f"Erro: Usuário com e-mail '{email}' não encontrado.", file=sys.stderr)
        return 1

    password = getattr(args, "password", None)
    if not password:
        password = getpass.getpass("Digite a nova senha (mínimo 10 caracteres): ")
        confirmation = getpass.getpass("Confirme a nova senha: ")
        if password != confirmation:
            print("Erro: As senhas não conferem.", file=sys.stderr)
            return 1

    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Erro: A senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.", file=sys.stderr)
        return 1

    pwd_hash = hash_password(password)
    updated_user = User(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        name=user.name,
        password_hash=pwd_hash,
        role=user.role,
        created_at=user.created_at,
    )
    user_repo.save_user(updated_user)
    print(f"Senha atualizada com sucesso para {email}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Administração de Tenants e Usuários do Pauta")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-tenant
    tenant_parser = subparsers.add_parser("create-tenant", help="Cria uma nova organização/escola")
    tenant_parser.add_argument("name", help="Nome da escola ou organização")
    tenant_parser.add_argument("--minutes", type=int, default=300, help="Cota mensal em minutos de áudio (padrão: 300)")
    tenant_parser.add_argument("--id", help="ID personalizado para o tenant (opcional)")

    # create-user
    user_parser = subparsers.add_parser("create-user", help="Cria um novo usuário vinculado a um tenant")
    user_parser.add_argument("--tenant", required=True, help="ID do tenant")
    user_parser.add_argument("--email", required=True, help="E-mail de login")
    user_parser.add_argument("--name", required=True, help="Nome completo")
    user_parser.add_argument("--role", required=True, choices=["owner", "teacher"], help="Papel do usuário")
    user_parser.add_argument("--password", help="Senha (opcional, se omitido usa getpass)")

    # reset-password
    pwd_parser = subparsers.add_parser("reset-password", help="Redefine a senha de um usuário existente")
    pwd_parser.add_argument("--email", required=True, help="E-mail do usuário")
    pwd_parser.add_argument("--password", help="Nova senha (opcional, se omitido usa getpass)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create-tenant":
        return handle_create_tenant(args)
    if args.command == "create-user":
        return handle_create_user(args)
    if args.command == "reset-password":
        return handle_reset_password(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
