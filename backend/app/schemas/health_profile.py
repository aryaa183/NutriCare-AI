from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


class HealthProfileRequest(BaseModel):
    age: int = Field(ge=13, le=100)
    gender: Literal["male", "female"]
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=25, le=300)
    activity_level: Literal["sedentary", "light", "moderate", "active"]
    goal: Literal["weight_loss", "weight_gain", "general"]

    diet_type: Literal["vegetarian", "non_vegetarian", "eggetarian", "vegan"] = "vegetarian"
    regional_preference: Optional[str] = None
    budget_level: Optional[Literal["low", "medium", "flexible"]] = None
    max_cooking_time: Optional[int] = Field(default=None, ge=5, le=300)

    allergies: list[str] = Field(default_factory=list)
    conditions: list[Literal["diabetes", "hypertension", "heart_disease"]] = Field(default_factory=list)

    @field_validator("allergies")
    @classmethod
    def validate_allergies(cls, v):
        allowed = {"peanut", "dairy", "egg", "gluten", "soy", "tree_nut", "fish", "shellfish", "sesame", "mustard"}
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"Unknown allergy type(s): {invalid}. Allowed: {allowed}")
        return v


class NutritionTargets(BaseModel):
    daily_calorie_target: float
    protein_target_g: float
    carb_target_g: float
    fat_target_g: float
    fiber_target_g: float


class HealthProfileResponse(HealthProfileRequest):
    nutrition_targets: NutritionTargets
