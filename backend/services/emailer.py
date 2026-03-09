# -*- coding: utf-8 -*-
"""Envoi d'emails transactionnels (Resend)."""

from __future__ import annotations

import os
from typing import Any

from utils.logger import get_logger

logger = get_logger("clipai.email")

try:
    import resend
except Exception:  # pragma: no cover
    resend = None


EMAIL_TEMPLATES = {
    "welcome": """
        <h1>Bienvenue sur ClipAI</h1>
        <p>Ton studio de generation de clips est pret.</p>
    """,
    "clips_ready": """
        <h1>Tes clips sont prets</h1>
        <p>Connecte-toi pour les telecharger et les publier.</p>
    """,
    "payment_success": """
        <h1>Paiement confirme</h1>
        <p>Ton abonnement est actif. Merci pour ta confiance.</p>
    """,
    "security_alert": """
        <h1>Alerte securite</h1>
        <p>Une connexion inhabituelle a ete detectee sur ton compte.</p>
    """,
}


def render_email_template(template_key: str, context: dict[str, Any] | None = None) -> str:
    template = EMAIL_TEMPLATES.get(template_key, "<p>Notification ClipAI</p>")
    context = context or {}
    html = template
    for key, value in context.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html


def send_transactional_email(
    *,
    to_email: str,
    subject: str,
    template_key: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    html = render_email_template(template_key, context=context)
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RESEND_FROM", "ClipAI <no-reply@clipai.local>")

    if not resend or not api_key:
        logger.info(
            "email_skipped",
            extra={"to_email": to_email, "subject": subject, "template_key": template_key},
        )
        return {"sent": False, "provider": "none"}

    resend.api_key = api_key
    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    response = resend.Emails.send(payload)
    logger.info(
        "email_sent",
        extra={"to_email": to_email, "subject": subject, "template_key": template_key},
    )
    return {"sent": True, "provider": "resend", "response": response}

