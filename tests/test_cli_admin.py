from argparse import Namespace
import pytest

from telecom.accounts.models import Tenant
from telecom.accounts.passwords import verify_password
from telecom.cli.admin import (
    handle_create_tenant,
    handle_create_user,
    handle_reset_password,
    main,
)
from telecom.storage.db import Database
from telecom.storage.repositories import UserRepository


def test_cli_create_tenant(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = UserRepository(db)

    args = Namespace(name="Escola X", minutes=600, id="escola-x")
    res = handle_create_tenant(args, repo=repo)
    assert res == 0

    tenant = repo.get_tenant("escola-x")
    assert tenant is not None
    assert tenant.name == "Escola X"
    assert tenant.monthly_audio_minutes == 600


def test_cli_create_user_and_validation(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = UserRepository(db)
    repo.save_tenant(Tenant(id="escola-x", name="Escola X"))

    # Sucesso
    args = Namespace(tenant="escola-x", email="ana@escola.com", name="Ana", role="owner", password="senha-muito-segura")
    res = handle_create_user(args, repo=repo)
    assert res == 0

    user = repo.get_user_by_email("ana@escola.com")
    assert user is not None
    assert user.name == "Ana"
    assert user.role == "owner"
    assert verify_password("senha-muito-segura", user.password_hash) is True

    # Rejeita tenant inexistente
    args_bad_tenant = Namespace(tenant="inexistente", email="b@b.com", name="B", role="teacher", password="senha-muito-segura")
    assert handle_create_user(args_bad_tenant, repo=repo) == 1

    # Rejeita e-mail duplicado
    args_dup = Namespace(tenant="escola-x", email="ana@escola.com", name="Outra Ana", role="teacher", password="senha-muito-segura")
    assert handle_create_user(args_dup, repo=repo) == 1

    # Rejeita senha curta (< 10 chars)
    args_short = Namespace(tenant="escola-x", email="curto@escola.com", name="Curto", role="teacher", password="123")
    assert handle_create_user(args_short, repo=repo) == 1


def test_cli_reset_password(tmp_path):
    db = Database(tmp_path / "test.db")
    repo = UserRepository(db)
    repo.save_tenant(Tenant(id="escola-x", name="Escola X"))

    # Cria usuário inicial
    handle_create_user(
        Namespace(tenant="escola-x", email="ana@escola.com", name="Ana", role="owner", password="senha-antiga-123"),
        repo=repo,
    )

    # Reset de senha
    reset_args = Namespace(email="ana@escola.com", password="senha-nova-456789")
    res = handle_reset_password(reset_args, repo=repo)
    assert res == 0

    updated = repo.get_user_by_email("ana@escola.com")
    assert verify_password("senha-antiga-123", updated.password_hash) is False
    assert verify_password("senha-nova-456789", updated.password_hash) is True

    # Rejeita e-mail inexistente
    bad_email_args = Namespace(email="fantasma@escola.com", password="senha-nova-456789")
    assert handle_reset_password(bad_email_args, repo=repo) == 1
