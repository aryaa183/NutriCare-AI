from pydantic import BaseModel
from typing import Literal


class RecommendationItem(BaseModel):
    recipe_id: int
    recipe_name: str
    region: str
    calories: float
    protein_g: float
    cooking_time_mins: float
    score: float
    why: str
    meal_calorie_target: float


class FeedbackRequest(BaseModel):
    recipe_id: int
    interaction_type: Literal["like", "dislike"]
    rating: int | None = None


class MealLogRequest(BaseModel):
    recipe_id: int
    meal_type: Literal["Breakfast", "Lunch", "Snack", "Dinner"]
    consumed: bool = True
