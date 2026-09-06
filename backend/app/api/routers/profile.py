from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.schemas.health_profile import HealthProfileRequest, HealthProfileResponse, NutritionTargets
from app.services.nutrition_service import compute_daily_targets
from app.api.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


def _upsert_profile(db: Session, user: models.User, payload: HealthProfileRequest) -> HealthProfileResponse:
    targets = compute_daily_targets(
        weight_kg=payload.weight_kg, height_cm=payload.height_cm,
        age=payload.age, gender=payload.gender,
        activity_level=payload.activity_level, goal=payload.goal,
    )

    hp = user.health_profile or models.HealthProfile(user_id=user.id)
    hp.age = payload.age
    hp.gender = payload.gender
    hp.height_cm = payload.height_cm
    hp.weight_kg = payload.weight_kg
    hp.activity_level = payload.activity_level
    hp.goal = payload.goal
    hp.daily_calorie_target = targets["daily_calorie_target"]
    hp.protein_target_g = targets["protein_target_g"]
    hp.carb_target_g = targets["carb_target_g"]
    hp.fat_target_g = targets["fat_target_g"]
    hp.fiber_target_g = targets["fiber_target_g"]
    db.add(hp)

    prefs = user.preferences or models.UserPreference(user_id=user.id)
    prefs.diet_type = payload.diet_type
    prefs.regional_preference = payload.regional_preference
    prefs.budget_level = payload.budget_level
    prefs.max_cooking_time = payload.max_cooking_time
    db.add(prefs)

    # allergies / conditions: replace wholesale on each save — simpler and
    # safer than diffing, and this endpoint represents "the current state
    # of the user's profile", not an incremental patch.
    db.query(models.UserAllergy).filter(models.UserAllergy.user_id == user.id).delete()
    for a in payload.allergies:
        db.add(models.UserAllergy(user_id=user.id, allergy_type=a))

    db.query(models.UserHealthCondition).filter(models.UserHealthCondition.user_id == user.id).delete()
    for c in payload.conditions:
        db.add(models.UserHealthCondition(user_id=user.id, condition=c))

    db.commit()
    db.refresh(hp)

    return HealthProfileResponse(
        **payload.model_dump(),
        nutrition_targets=NutritionTargets(
            daily_calorie_target=hp.daily_calorie_target,
            protein_target_g=hp.protein_target_g,
            carb_target_g=hp.carb_target_g,
            fat_target_g=hp.fat_target_g,
            fiber_target_g=hp.fiber_target_g,
        ),
    )


@router.post("", response_model=HealthProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: HealthProfileRequest, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    return _upsert_profile(db, current_user, payload)


@router.put("", response_model=HealthProfileResponse)
def update_profile(payload: HealthProfileRequest, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    if current_user.health_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile yet — use POST /profile first")
    return _upsert_profile(db, current_user, payload)


@router.get("", response_model=HealthProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    hp = current_user.health_profile
    if hp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not set up yet")
    prefs = current_user.preferences

    return HealthProfileResponse(
        age=hp.age, gender=hp.gender, height_cm=hp.height_cm, weight_kg=hp.weight_kg,
        activity_level=hp.activity_level, goal=hp.goal,
        diet_type=prefs.diet_type if prefs else "vegetarian",
        regional_preference=prefs.regional_preference if prefs else None,
        budget_level=prefs.budget_level if prefs else None,
        max_cooking_time=prefs.max_cooking_time if prefs else None,
        allergies=[a.allergy_type for a in current_user.allergies],
        conditions=[c.condition for c in current_user.conditions],
        nutrition_targets=NutritionTargets(
            daily_calorie_target=hp.daily_calorie_target,
            protein_target_g=hp.protein_target_g,
            carb_target_g=hp.carb_target_g,
            fat_target_g=hp.fat_target_g,
            fiber_target_g=hp.fiber_target_g,
        ),
    )
