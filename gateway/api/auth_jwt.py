from __future__ import annotations

import time
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja.security import HttpBearer


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + int(getattr(settings, "JWT_EXPIRE_SECONDS", 86400)),
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


class JWTAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        payload = decode_token(token)
        if not payload:
            return None
        return payload.get("sub")
