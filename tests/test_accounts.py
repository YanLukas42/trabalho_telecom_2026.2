import pytest

from telecom.accounts.models import Principal, Tenant, User
from telecom.accounts.passwords import hash_password, verify_password


def test_hash_and_verify_password():
    raw = "senhaForte123!"
    hashed = hash_password(raw)
    assert hashed.startswith("scrypt$")
    assert verify_password(raw, hashed) is True
    assert verify_password("senhaErrada", hashed) is False
    assert verify_password("", hashed) is False


def test_password_minimum_length():
    with pytest.raises(ValueError, match="mínimo 10 caracteres"):
        hash_password("curta123")


def test_models_are_frozen():
    principal = Principal(tenant_id="t1", user_id="u1", role="teacher")
    with pytest.raises(Exception):
        principal.role = "owner"  # type: ignore

    tenant = Tenant(id="t1", name="Escola")
    assert tenant.created_at != ""
    with pytest.raises(Exception):
        tenant.name = "Outra"  # type: ignore

    user = User(id="u1", tenant_id="t1", email="a@a.com", name="Ana", role="teacher", password_hash="hash")
    assert user.created_at != ""
    with pytest.raises(Exception):
        user.name = "Bia"  # type: ignore
