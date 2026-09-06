from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.schemas.recommendation import FeedbackRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # A user can change their mind — remove any prior feedback on this
    # recipe before recording the new one, rather than accumulating
    # contradictory rows that would confuse the scoring logic.
    db.query(models.UserFeedback).filter(
        models.UserFeedback.user_id == current_user.id,
        models.UserFeedback.recipe_id == payload.recipe_id,
    ).delete()

    fb = models.UserFeedback(
        user_id=current_user.id,
        recipe_id=payload.recipe_id,
        interaction_type=payload.interaction_type,
        rating=payload.rating,
    )
    db.add(fb)
    db.commit()
    return {"detail": "Feedback recorded", "recipe_id": payload.recipe_id, "interaction_type": payload.interaction_type}
