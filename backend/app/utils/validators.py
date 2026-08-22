"""Registration password and Indian mobile rules."""

from __future__ import annotations

import re

_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


class PasswordPolicyError(ValueError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_mobile(mobile: str) -> str:
    digits = re.sub(r"\D", "", mobile)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits


def validate_mobile(mobile: str) -> str:
    normalized = normalize_mobile(mobile)
    if not _MOBILE_RE.fullmatch(normalized):
        raise ValueError("Mobile must be a 10-digit Indian number")
    return normalized


def validate_password_strength(password: str) -> None:
    if len(password) < 12:
        raise PasswordPolicyError("Password must be at least 12 characters")
    if password.lower() == password or password.upper() == password:
        raise PasswordPolicyError("Password must include upper and lower case letters")
    if not any(ch.isdigit() for ch in password):
        raise PasswordPolicyError("Password must include a digit")
    if not any(not ch.isalnum() for ch in password):
        raise PasswordPolicyError("Password must include a symbol")
