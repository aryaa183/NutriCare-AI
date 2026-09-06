from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.db import models
from app.services.recommendation_service import RecipeStore
from app.api.deps import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    hp = current_user.health_profile
    if hp is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete your health profile first")

    today = datetime.now(timezone.utc).date()
    todays_logs = [
        l for l in current_user.meal_logs
        if l.consumed and l.consumed_at.date() == today
    ]

    recipe_df = RecipeStore.get()
    consumed_calories = 0.0
    consumed_protein = 0.0
    meals_today = []
    for log in todays_logs:
        match = recipe_df[recipe_df["recipe_id"] == log.recipe_id]
        if not match.empty:
            row = match.iloc[0]
            consumed_calories += float(row["calories"])
            consumed_protein += float(row["protein_g"])
            meals_today.append({
                "meal_type": log.meal_type,
                "recipe_name": row["recipe_name"],
                "calories": float(row["calories"]),
                "protein_g": float(row["protein_g"]),
            })

    return {
        "daily_calorie_target": hp.daily_calorie_target,
        "calories_consumed": round(consumed_calories, 1),
        "calories_remaining": round(hp.daily_calorie_target - consumed_calories, 1),
        "protein_target_g": hp.protein_target_g,
        "protein_consumed_g": round(consumed_protein, 1),
        "protein_remaining_g": round(hp.protein_target_g - consumed_protein, 1),
        "meals_today": meals_today,
    }
