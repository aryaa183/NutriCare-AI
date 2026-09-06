from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db import models
from app.schemas.recommendation import MealLogRequest
from app.services.recommendation_service import RecipeStore
from app.api.deps import get_current_user

router = APIRouter(tags=["meals"])


@router.get("/recipes")
def list_recipes(
    meal_type: Optional[str] = None,
    region: Optional[str] = None,
    diet_type: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    df = RecipeStore.get()
    result = df
    if meal_type:
        result = result[result["meal_type"].str.contains(meal_type, case=False, na=False)]
    if region:
        result = result[result["region"] == region]
    if diet_type:
        result = result[result["diet_type"] == diet_type]
    cols = ["recipe_id", "recipe_name", "meal_type", "region", "diet_type", "calories", "protein_g"]
    return result[cols].head(limit).to_dict(orient="records")


@router.get("/recipes/search")
def search_recipes(q: str, limit: int = Query(default=20, le=100)):
    df = RecipeStore.get()
    result = df[df["recipe_name"].str.contains(q, case=False, na=False)]
    cols = ["recipe_id", "recipe_name", "meal_type", "region", "diet_type", "calories", "protein_g"]
    return result[cols].head(limit).to_dict(orient="records")


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    df = RecipeStore.get()
    match = df[df["recipe_id"] == recipe_id]
    if match.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return match.iloc[0].to_dict()


@router.post("/meals/log", status_code=status.HTTP_201_CREATED)
def log_meal(
    payload: MealLogRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    log = models.MealLog(
        user_id=current_user.id,
        recipe_id=payload.recipe_id,
        meal_type=payload.meal_type,
        consumed=payload.consumed,
    )
    db.add(log)
    db.commit()
    return {"detail": "Meal logged", "recipe_id": payload.recipe_id}


@router.get("/meals/history")
def meal_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
):
    logs = (
        db.query(models.MealLog)
        .filter(models.MealLog.user_id == current_user.id)
        .order_by(models.MealLog.consumed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"recipe_id": l.recipe_id, "meal_type": l.meal_type, "consumed": l.consumed, "consumed_at": l.consumed_at}
        for l in logs
    ]
