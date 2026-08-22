"""Password hashing, session tokens, and authenticated secret encryption.

Never log passwords, TOTP, API secrets, or access tokens.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_HASHER = PasswordHasher()
_AAD = b"gnkalgo-v1"


def hash_password(password: str) -> str:
    return _HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _HASHER.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _aes_key(encryption_key: str) -> bytes:
    return hashlib.sha256(encryption_key.encode("utf-8")).digest()


def encrypt_secret(plaintext: str, encryption_key: str) -> str:
    """Encrypt a secret with AES-GCM. Ciphertext is stored; plaintext is never logged."""
    if not plaintext:
        raise ValueError("plaintext must not be empty")
    if not encryption_key:
        raise ValueError("encryption_key must not be empty")
    nonce = os.urandom(12)
    aes = AESGCM(_aes_key(encryption_key))
    packed = nonce + aes.encrypt(nonce, plaintext.encode("utf-8"), _AAD)
    return base64.urlsafe_b64encode(packed).decode("ascii")


def decrypt_secret(ciphertext: str, encryption_key: str) -> str:
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    nonce, data = raw[:12], raw[12:]
    aes = AESGCM(_aes_key(encryption_key))
    return aes.decrypt(nonce, data, _AAD).decode("utf-8")
