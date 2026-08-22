"""Password hashing and AES-GCM helpers. Never assert plaintext secrets in logs."""

import pytest

from app.core.security import (
    decrypt_secret,
    encrypt_secret,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.utils.validators import (
    PasswordPolicyError,
    normalize_email,
    validate_mobile,
    validate_password_strength,
)


def test_password_hash_is_not_plaintext() -> None:
    password = "StrongPass!2345"
    digest = hash_password(password)
    assert digest != password
    assert "StrongPass" not in digest
    assert verify_password(digest, password) is True
    assert verify_password(digest, "wrong-password") is False


def test_encrypt_secret_roundtrip() -> None:
    token = "dhan-access-token-example"
    key = "test-encryption-key"
    packed = encrypt_secret(token, key)
    assert token not in packed
    assert decrypt_secret(packed, key) == token


def test_session_token_hash_is_sha256_hex() -> None:
    digest = hash_session_token("opaque-cookie-value")
    assert len(digest) == 64
    assert digest != "opaque-cookie-value"


def test_password_policy() -> None:
    validate_password_strength("Abcdefghijk1!")
    with pytest.raises(PasswordPolicyError):
        validate_password_strength("short1!")
    with pytest.raises(PasswordPolicyError):
        validate_password_strength("alllowercase1!")


def test_mobile_and_email_normalize() -> None:
    assert validate_mobile("9876543210") == "9876543210"
    assert validate_mobile("+91 98765 43210") == "9876543210"
    with pytest.raises(ValueError):
        validate_mobile("12345")
    assert normalize_email("  A@B.com ") == "a@b.com"
