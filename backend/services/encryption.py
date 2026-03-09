# -*- coding: utf-8 -*-
"""Services de chiffrement et de masquage des donnees sensibles."""

from __future__ import annotations

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _master_key_material() -> bytes:
    raw = os.getenv("ENCRYPTION_MASTER_KEY", "").strip()
    if not raw:
        raw = os.getenv("JWT_SECRET", "").strip()
    if not raw:
        raw = "clipai-dev-master-key"
    return raw.encode("utf-8")


@lru_cache(maxsize=1)
def _base_key() -> bytes:
    salt = os.getenv("ENCRYPTION_SALT", "clipai-default-salt").encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return kdf.derive(_master_key_material())


def _derive_key(context: str) -> bytes:
    digest = hashlib.sha256(context.encode("utf-8")).digest()
    return hashlib.pbkdf2_hmac("sha256", _base_key(), digest, 120000, dklen=32)


def encrypt_text(value: str, *, context: str = "global") -> str:
    """Chiffre une valeur texte avec AES-256-GCM et renvoie du base64."""
    data = (value or "").encode("utf-8")
    key = _derive_key(context)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, data, None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode("utf-8")


def decrypt_text(token: str, *, context: str = "global") -> str:
    """Dechiffre une valeur base64 produite par encrypt_text."""
    raw = base64.urlsafe_b64decode(token.encode("utf-8"))
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(_derive_key(context))
    clear = aesgcm.decrypt(nonce, ciphertext, None)
    return clear.decode("utf-8")


def derive_user_key(user_id: str) -> str:
    """Renvoie une cle derivee stable par utilisateur (hex)."""
    return hashlib.sha256(_derive_key(f"user:{user_id}")).hexdigest()


def mask_email(email: str) -> str:
    """Masque partiellement un email pour les logs publics."""
    if "@" not in (email or ""):
        return "***"
    local, domain = email.split("@", maxsplit=1)
    if "." in domain:
        root, tld = domain.rsplit(".", maxsplit=1)
        return f"{(local[:2] or '*')}***@{(root[:2] or '*')}***.{tld}"
    return f"{(local[:2] or '*')}***@***"


def mask_ip(ip: str) -> str:
    """Masque une IPv4/IPv6 pour eviter les fuites en logs."""
    if not ip:
        return "***"
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:2] + ["***", "***"])
    chunks = ip.split(".")
    if len(chunks) == 4:
        return f"{chunks[0]}.{chunks[1]}.***.***"
    return "***"


def redact_sensitive_dict(payload: dict) -> dict:
    """Masque les champs sensibles avant log JSON."""
    blocked = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "authorization",
    }
    result: dict = {}
    for key, value in (payload or {}).items():
        if key.lower() in blocked:
            result[key] = "***REDACTED***"
            continue
        result[key] = value
    return result
