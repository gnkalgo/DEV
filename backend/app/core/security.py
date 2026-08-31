import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except (TypeError, ValueError, UnknownHashError):
        pass

    if not hashed:
        return False

    # Older deployments stored a plain SHA-256 hex digest, which Passlib cannot
    # identify. Keep compatibility for those records until they are rehashed.
    legacy_candidates = (
        hashlib.sha256(plain.encode()).hexdigest(),
        hashlib.sha512(plain.encode()).hexdigest(),
        hashlib.md5(plain.encode()).hexdigest(),
    )
    return any(hmac.compare_digest(candidate, hashed) for candidate in legacy_candidates)


def password_needs_rehash(hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return pwd_context.identify(hashed) is None
    except (TypeError, ValueError, UnknownHashError):
        return True


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.encryption_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_data(data: str) -> str:
    return _fernet().encrypt(data.encode()).decode()


def decrypt_data(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expire


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_token(plain), hashed)


def generate_secure_token() -> str:
    return secrets.token_urlsafe(32)
