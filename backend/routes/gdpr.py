# -*- coding: utf-8 -*-
"""Routes RGPD (export et suppression/anonymisation de compte)."""


import json
import os
import tempfile
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from database.connection import delete_record, get_record, list_records, update_record
from services.audit import log_audit
from services.auth_security import revoke_all_user_sessions, verify_password
from utils.auth import require_current_user
from utils.helpers import utc_now_iso

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


def _user_export_payload(user_id: str) -> dict:
    return {
        "profile": get_record("users", user_id) or {},
        "videos": [row for row in list_records("videos") if row.get("user_id") == user_id],
        "clips": [row for row in list_records("clips") if row.get("user_id") == user_id],
        "payments": [
            row for row in list_records("subscriptions") if row.get("user_id") == user_id
        ],
        "audit_logs": [row for row in list_records("audit_logs") if row.get("user_id") == user_id],
    }


@router.get("/export")
def export_user_data(
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> FileResponse:
    payload = _user_export_payload(current_user["id"])
    export_root = os.path.join(tempfile.gettempdir(), "clipai_gdpr_exports")
    os.makedirs(export_root, exist_ok=True)
    zip_path = os.path.join(export_root, f"gdpr_export_{current_user['id']}.zip")

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("profile.json", json.dumps(payload["profile"], ensure_ascii=False, indent=2))
        archive.writestr("videos.json", json.dumps(payload["videos"], ensure_ascii=False, indent=2))
        archive.writestr("clips.json", json.dumps(payload["clips"], ensure_ascii=False, indent=2))
        archive.writestr("payments.json", json.dumps(payload["payments"], ensure_ascii=False, indent=2))
        archive.writestr(
            "audit_logs.json",
            json.dumps(payload["audit_logs"], ensure_ascii=False, indent=2),
        )

    log_audit(
        action="gdpr.export",
        success=True,
        user_id=current_user["id"],
        resource_type="user",
        resource_id=current_user["id"],
        request=request,
    )
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"clipai_gdpr_export_{current_user['id']}.zip",
    )


@router.delete("/delete-account")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    user = get_record("users", current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not verify_password(payload.password, user.get("password_hash", "")):
        log_audit(
            action="gdpr.delete_account.failed",
            success=False,
            user_id=current_user["id"],
            request=request,
        )
        raise HTTPException(status_code=401, detail="Mot de passe invalide")

    for video in list_records("videos"):
        if video.get("user_id") == current_user["id"]:
            delete_record("videos", video["id"])

    for clip in list_records("clips"):
        if clip.get("user_id") == current_user["id"]:
            delete_record("clips", clip["id"])

    revoke_all_user_sessions(current_user["id"])
    update_record(
        "users",
        current_user["id"],
        {
            "email": f"deleted-{current_user['id']}@anonymous.local",
            "full_name": "Deleted User",
            "password_hash": "",
            "avatar_url": "",
            "bio": "",
            "is_deleted": True,
            "deleted_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        },
    )

    log_audit(
        action="gdpr.delete_account",
        success=True,
        user_id=current_user["id"],
        resource_type="user",
        resource_id=current_user["id"],
        request=request,
    )
    return {"message": "Compte anonymise conformement au RGPD"}

