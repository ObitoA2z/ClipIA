# -*- coding: utf-8 -*-
"""Service d'audit centralise (logs securite et actions sensibles)."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from database.connection import insert_record, list_records
from services.auth_security import get_client_ip, get_country
from services.encryption import mask_email, mask_ip, redact_sensitive_dict
from utils.helpers import new_id, utc_now_iso
from utils.logger import get_logger

logger = get_logger("clipai.audit")


def create_audit_event(
    *,
    action: str,
    success: bool,
    user_id: str | None = None,
    admin_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    country: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": new_id(),
        "user_id": user_id,
        "admin_id": admin_id,
        "action": action,
        "resource_type": resource_type or "",
        "resource_id": resource_id,
        "ip_address": ip_address or "",
        "user_agent": user_agent or "",
        "country": (country or "ZZ").upper(),
        "success": bool(success),
        "metadata": metadata or {},
        "created_at": utc_now_iso(),
    }


def log_audit(
    *,
    action: str,
    success: bool = True,
    user_id: str | None = None,
    admin_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ip_address = get_client_ip(request) if request else ""
    user_agent = request.headers.get("user-agent", "") if request else ""
    country = get_country(request) if request else "ZZ"

    event = create_audit_event(
        action=action,
        success=success,
        user_id=user_id,
        admin_id=admin_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        country=country,
        metadata=metadata or {},
    )
    insert_record("audit_logs", event["id"], event)

    safe_payload = redact_sensitive_dict(
        {
            "action": action,
            "success": success,
            "user_id": user_id,
            "admin_id": admin_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": mask_ip(ip_address),
            "country": country,
            "metadata": metadata or {},
        }
    )
    logger.info("audit_event", extra=safe_payload)
    return event


def notify_security_event(
    *,
    event_type: str,
    email: str,
    details: dict[str, Any] | None = None,
) -> None:
    safe_email = mask_email(email)
    logger.warning(
        "security_alert",
        extra={
            "event_type": event_type,
            "email": safe_email,
            "details": redact_sensitive_dict(details or {}),
        },
    )


def detect_abuse_signals(*, user_id: str) -> dict[str, Any]:
    now_iso = utc_now_iso()
    recent_video_events = [
        item
        for item in list_records("audit_logs")
        if item.get("user_id") == user_id and item.get("action") == "video.process.started"
    ]
    too_many_videos = len(recent_video_events) >= 20
    return {
        "checked_at": now_iso,
        "too_many_videos": too_many_videos,
        "events_count": len(recent_video_events),
    }

