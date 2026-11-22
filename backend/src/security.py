"""Authentication cryptography helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

PASSWORD_HASHER = PasswordHasher()


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def issue_access_token(user_id: UUID, secret: str, issuer: str, minutes: int = 15) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iss": issuer,
        "aud": "onisagent-api",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_access_token(token: str, secret: str, issuer: str) -> UUID:
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=issuer,
        audience="onisagent-api",
        options={"require": ["sub", "exp", "iss", "aud"]},
    )
    return UUID(str(payload["sub"]))
