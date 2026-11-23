"""Criptografia e verificação de senhas com hashlib.scrypt (stdlib).

# shortcut: hashlib.scrypt sem 2FA no MVP, trocar por OIDC ao abrir cadastro público (ADR-0002)
"""

import hashlib
import hmac
import secrets

MIN_PASSWORD_LENGTH = 10
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Gera hash scrypt com salt aleatório. Exige senha com pelo menos 10 caracteres."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres.")

    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash gerado por hash_password."""
    if not stored_hash or not stored_hash.startswith("scrypt$"):
        return False

    parts = stored_hash.split("$")
    if len(parts) != 6:
        return False

    try:
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])

        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
        )
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Gera hash SHA-256 do token de sessão para armazenamento seguro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
