# -*- coding: utf-8 -*-
"""Routes collaboration equipe (plan business)."""


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import find_one, get_record, insert_record, list_records
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class TeamInviteRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: str = Field(pattern="^(owner|editor|viewer)$")


def _require_business_plan(user: dict) -> None:
    if user.get("plan") not in {"business"} and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Fonction reservee au plan Business")


@router.post("")
def create_team(payload: TeamCreateRequest, current_user: dict = Depends(require_current_user)) -> dict:
    _require_business_plan(current_user)
    team_id = new_id()
    insert_record(
        "teams",
        team_id,
        {
            "id": team_id,
            "owner_id": current_user["id"],
            "name": payload.name,
            "created_at": utc_now_iso(),
        },
    )
    member_id = new_id()
    insert_record(
        "team_members",
        member_id,
        {
            "id": member_id,
            "team_id": team_id,
            "user_id": current_user["id"],
            "role": "owner",
            "invited_email": current_user["email"],
            "created_at": utc_now_iso(),
        },
    )
    return {"team_id": team_id, "name": payload.name}


@router.get("")
def list_teams(current_user: dict = Depends(require_current_user)) -> dict:
    memberships = [row for row in list_records("team_members") if row.get("user_id") == current_user["id"]]
    team_ids = {row.get("team_id") for row in memberships}
    teams = [row for row in list_records("teams") if row.get("id") in team_ids]
    return {"teams": teams, "memberships": memberships}


@router.post("/{team_id}/invite")
def invite_member(
    team_id: str,
    payload: TeamInviteRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    team = get_record("teams", team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team introuvable")
    if team.get("owner_id") != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Seul le owner peut inviter")

    invited_user = find_one("users", "email", payload.email.lower().strip())
    member_id = new_id()
    insert_record(
        "team_members",
        member_id,
        {
            "id": member_id,
            "team_id": team_id,
            "user_id": invited_user.get("id") if invited_user else None,
            "role": payload.role,
            "invited_email": payload.email.lower().strip(),
            "created_at": utc_now_iso(),
        },
    )
    return {"message": "Invitation enregistree", "member_id": member_id}

