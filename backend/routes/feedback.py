# -*- coding: utf-8 -*-
"""Routes feedback utilisateur, NPS et demandes de features."""


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import get_record, insert_record, list_records, update_record
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreateRequest(BaseModel):
    type: str = Field(pattern="^(bug|suggestion|compliment|nps)$")
    rating: int | None = Field(default=None, ge=0, le=10)
    message: str = Field(min_length=1, max_length=2000)
    page_url: str | None = Field(default=None, max_length=500)


class FeatureRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=2000)


@router.post("")
def create_feedback(
    payload: FeedbackCreateRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    feedback_id = new_id()
    insert_record(
        "feedback",
        feedback_id,
        {
            "id": feedback_id,
            "user_id": current_user["id"],
            "type": payload.type,
            "rating": payload.rating,
            "message": payload.message,
            "page_url": payload.page_url or "",
            "created_at": utc_now_iso(),
        },
    )
    return {"message": "Feedback enregistre", "id": feedback_id}


@router.get("/nps")
def get_nps(current_user: dict = Depends(require_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acces admin requis")
    responses = [row for row in list_records("feedback") if row.get("type") == "nps" and row.get("rating") is not None]
    if not responses:
        return {"score": 0, "total": 0}
    promoters = len([row for row in responses if int(row["rating"]) >= 9])
    detractors = len([row for row in responses if int(row["rating"]) <= 6])
    total = len(responses)
    score = round(((promoters - detractors) / total) * 100, 2)
    return {"score": score, "total": total, "promoters": promoters, "detractors": detractors}


@router.get("/requests")
def list_feature_requests() -> dict:
    rows = list_records("feature_requests")
    rows.sort(key=lambda item: item.get("votes_count", 0), reverse=True)
    return {"items": rows}


@router.post("/requests")
def create_feature_request(
    payload: FeatureRequestCreate,
    current_user: dict = Depends(require_current_user),
) -> dict:
    req_id = new_id()
    insert_record(
        "feature_requests",
        req_id,
        {
            "id": req_id,
            "title": payload.title,
            "description": payload.description,
            "status": "requested",
            "votes_count": 0,
            "created_by": current_user["id"],
            "created_at": utc_now_iso(),
        },
    )
    return {"message": "Feature request creee", "id": req_id}


@router.post("/requests/{feature_id}/vote")
def vote_feature_request(
    feature_id: str,
    current_user: dict = Depends(require_current_user),
) -> dict:
    feature = get_record("feature_requests", feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature request introuvable")

    vote_id = f"{current_user['id']}:{feature_id}"
    existing_vote = get_record("feature_votes", vote_id)
    if existing_vote:
        raise HTTPException(status_code=409, detail="Vote deja enregistre")

    insert_record(
        "feature_votes",
        vote_id,
        {
            "id": vote_id,
            "user_id": current_user["id"],
            "feature_id": feature_id,
            "created_at": utc_now_iso(),
        },
    )
    update_record(
        "feature_requests",
        feature_id,
        {"votes_count": int(feature.get("votes_count", 0)) + 1},
    )
    return {"message": "Vote enregistre"}

