from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Literal

from app.db.database import get_db
from app.db import models
from app.schemas.recommendation import RecommendationItem
from app.services.recommendation_service import recommend, RecommendationProfile
from app.api.deps import get_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

MEAL_TYPES = ["Breakfast", "Lunch", "Snack", "Dinner"]


def _build_profile(db: Session, user: models.User) -> RecommendationProfile:
    hp = user.health_profile
    if hp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your health profile (POST /profile) before requesting recommendations",
        )
    prefs = user.preferences

    liked = [f.recipe_id for f in user.feedback if f.interaction_type == "like"]
    disliked = [f.recipe_id for f in user.feedback if f.interaction_type == "dislike"]

    return RecommendationProfile(
        daily_calorie_target=hp.daily_calorie_target,
        diet_type=prefs.diet_type if prefs else "vegetarian",
        conditions=[c.condition for c in user.conditions],
        goal=hp.goal,
        allergies=[a.allergy_type for a in user.allergies],
        region_preference=prefs.regional_preference if prefs else None,
        max_cooking_time=prefs.max_cooking_time if prefs else None,
        liked_recipes=liked,
        disliked_recipes=disliked,
    )


@router.get("/today")
def recommendations_today(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = _build_profile(db, current_user)
    return {meal: recommend(profile, meal, top_n=3) for meal in MEAL_TYPES}


@router.get("/{meal_type}", response_model=list[RecommendationItem])
def recommendations_for_meal(
    meal_type: Literal["Breakfast", "Lunch", "Snack", "Dinner"],
    top_n: int = 5,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile = _build_profile(db, current_user)
    results = recommend(profile, meal_type, top_n=top_n)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recipes match your current constraints for this meal — try relaxing an allergy/time filter",
        )
    return results
