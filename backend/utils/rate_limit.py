# -*- coding: utf-8 -*-
"""Configuration centralisee du rate limiting (slowapi)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


def _key_func(request) -> str:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", maxsplit=1)[1].strip()
        if token:
            return f"token:{token}"
    return str(get_remote_address(request))


limiter = Limiter(key_func=_key_func, default_limits=["100/minute"])
