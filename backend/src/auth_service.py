"""Local authentication service with PBKDF2 password hashes and signed tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from src.database.json_storage import JsonStorage


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, storage: JsonStorage | None = None) -> None:
        self.storage = storage or JsonStorage()
        self.secret = os.getenv("AUTH_SECRET", "dev-only-change-this-secret").encode()
        self.ttl_seconds = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))

    @staticmethod
    def _hash(password: str, salt: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000).hex()

    @staticmethod
    def _public(user: dict[str, Any]) -> dict[str, Any]:
        return {"id": user["id"], "email": user["email"], "name": user["name"], "created_at": user["created_at"]}

    def register(self, email: str, password: str, name: str) -> tuple[dict[str, Any], str]:
        email = email.strip().casefold(); name = name.strip()
        if "@" not in email or len(email) > 254: raise AuthError("Email không hợp lệ.")
        if len(password) < 8: raise AuthError("Mật khẩu phải có ít nhất 8 ký tự.")
        if not name: raise AuthError("Tên hiển thị không được để trống.")
        if self.storage.find_user_by_email(email): raise AuthError("Email đã được đăng ký.")
        salt = secrets.token_bytes(16)
        user = self.storage.create_user(email=email, name=name, password_hash=self._hash(password, salt), salt=base64.urlsafe_b64encode(salt).decode())
        return self._public(user), self._issue(user["id"])

    def login(self, email: str, password: str) -> tuple[dict[str, Any], str]:
        user = self.storage.find_user_by_email(email)
        if not user:
            raise AuthError("Email hoặc mật khẩu không đúng.")
        salt = base64.urlsafe_b64decode(user["salt"].encode())
        if not hmac.compare_digest(self._hash(password, salt), user["password_hash"]):
            raise AuthError("Email hoặc mật khẩu không đúng.")
        return self._public(user), self._issue(user["id"])

    def _issue(self, user_id: str) -> str:
        payload = {"sub": user_id, "exp": int(time.time()) + self.ttl_seconds}
        raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
        signature = hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()
        return f"{raw}.{signature}"

    def verify(self, token: str) -> dict[str, Any]:
        try:
            raw, signature = token.split(".", 1)
            expected = hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected): raise AuthError("Token không hợp lệ.")
            payload = json.loads(base64.urlsafe_b64decode((raw + "===").encode()))
            if int(payload["exp"]) < int(time.time()): raise AuthError("Token đã hết hạn.")
            user = self.storage.get_user(payload["sub"])
            if not user: raise AuthError("Tài khoản không tồn tại.")
            return self._public(user)
        except (ValueError, KeyError, json.JSONDecodeError, base64.binascii.Error) as exc:
            raise AuthError("Token không hợp lệ.") from exc
