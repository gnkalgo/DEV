import hashlib

from app.core.security import verify_password


def test_verify_password_supports_legacy_sha256_hashes():
    password = "SecurePass1!"
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()

    assert verify_password(password, legacy_hash) is True
