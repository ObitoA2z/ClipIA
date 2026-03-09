# -*- coding: utf-8 -*-
"""Fonctions utilitaires de stockage mémoire (MVP local)."""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional

DATABASE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "users": {},
    "videos": {},
    "clips": {},
    "subscriptions": {},
    "sessions": {},
    "audit_logs": {},
    "push_subscriptions": {},
    "feature_flags": {},
    "referrals": {},
    "clip_comments": {},
    "api_keys": {},
    "feedback": {},
    "feature_requests": {},
    "feature_votes": {},
    "usage_logs": {},
    "teams": {},
    "team_members": {},
    "social_accounts": {},
    "scheduled_posts": {},
    "clip_performance": {},
    "brand_kits": {},
}

DB_LOCK = Lock()


def insert_record(table: str, record_id: str, payload: Dict[str, Any]) -> None:
    """Ajoute ou remplace un enregistrement en mémoire."""
    with DB_LOCK:
        DATABASE[table][record_id] = payload


def update_record(table: str, record_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Met à jour un enregistrement existant."""
    with DB_LOCK:
        record = DATABASE[table].get(record_id)
        if not record:
            return None
        record.update(updates)
        return dict(record)


def get_record(table: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Lit un enregistrement par son id."""
    with DB_LOCK:
        record = DATABASE[table].get(record_id)
        return dict(record) if record else None


def list_records(table: str) -> list[Dict[str, Any]]:
    """Renvoie tous les enregistrements de la table."""
    with DB_LOCK:
        return [dict(item) for item in DATABASE[table].values()]


def delete_record(table: str, record_id: str) -> bool:
    """Supprime un enregistrement. Renvoie True si trouvé."""
    with DB_LOCK:
        return DATABASE[table].pop(record_id, None) is not None


def find_one(table: str, key: str, value: Any) -> Optional[Dict[str, Any]]:
    """Cherche le premier enregistrement qui correspond à une clé/valeur."""
    with DB_LOCK:
        for item in DATABASE[table].values():
            if item.get(key) == value:
                return dict(item)
    return None
