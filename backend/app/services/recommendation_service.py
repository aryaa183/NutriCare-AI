"""
Recommendation Service — wraps the same hybrid engine validated in
ml/content_recommender.py, adapted for use inside the API (recipe
dataset loaded once at process start; per-request user profile assembled
from DB state by the router).
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional
from app.core.config import settings
from app.services.nutrition_service import compute_meal_calorie_target

ALLERGEN_COLS = {
    "peanut": "contains_peanut", "dairy": "contains_dairy", "egg": "contains_egg",
    "gluten": "contains_gluten", "soy": "contains_soy", "tree_nut": "contains_tree_nut",
    "fish": "contains_fish", "shellfish": "contains_shellfish",
    "sesame": "contains_sesame", "mustard": "contains_mustard",
}

CONDITION_RULES = {
    "diabetes": [
        {"field": "diabetic_friendly_tag", "equals": True, "weight": 12, "reason": "tagged diabetic-friendly"},
        {"field": "sugar_g", "max": 5, "weight": 10, "reason": "low sugar"},
        {"field": "fiber_g", "min": 4, "weight": 8, "reason": "good fiber content"},
    ],
    "hypertension": [
        {"field": "sodium_mg", "max": 400, "weight": 15, "reason": "low sodium"},
    ],
    "heart_disease": [
        {"field": "fat_g", "max": 15, "weight": 10, "reason": "moderate fat"},
        {"field": "sodium_mg", "max": 450, "weight": 8, "reason": "controlled sodium"},
        {"field": "fiber_g", "min": 4, "weight": 6, "reason": "heart-friendly fiber"},
    ],
    "weight_loss": [
        {"field": "calories", "max": 300, "weight": 8, "reason": "calorie-light option"},
        {"field": "fiber_g", "min": 4, "weight": 8, "reason": "keeps you fuller for longer"},
    ],
    "weight_gain": [
        {"field": "calories", "min": 300, "weight": 8, "reason": "calorie-dense option"},
        {"field": "protein_g", "min": 12, "weight": 8, "reason": "good protein for muscle gain"},
    ],
}


@dataclass
class RecommendationProfile:
    daily_calorie_target: float
    diet_type: str = "vegetarian"
    conditions: List[str] = field(default_factory=list)
    goal: str = "general"
    allergies: List[str] = field(default_factory=list)
    region_preference: Optional[str] = None
    max_cooking_time: Optional[int] = None
    liked_recipes: List[int] = field(default_factory=list)
    disliked_recipes: List[int] = field(default_factory=list)


class RecipeStore:
    """Loads the recipe dataset once; the API process holds it in memory
    rather than re-reading the CSV per request."""
    _df: Optional[pd.DataFrame] = None

    @classmethod
    def get(cls) -> pd.DataFrame:
        if cls._df is None:
            cls._df = pd.read_csv(settings.RECIPES_CSV_PATH)
        return cls._df

    @classmethod
    def reload(cls):
        cls._df = pd.read_csv(settings.RECIPES_CSV_PATH)


def _score_recipe(row: pd.Series, profile: RecommendationProfile, meal_target_kcal: float) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []

    diff_ratio = abs(row["calories"] - meal_target_kcal) / max(meal_target_kcal, 1)
    score += max(0, 20 - diff_ratio * 20)

    tags = list(profile.conditions) + ([profile.goal] if profile.goal in CONDITION_RULES else [])
    for tag in set(tags):
        for rule in CONDITION_RULES.get(tag, []):
            val = row[rule["field"]]
            hit = False
            if "equals" in rule and val == rule["equals"]:
                hit = True
            if "max" in rule and isinstance(val, (int, float)) and val <= rule["max"]:
                hit = True
            if "min" in rule and isinstance(val, (int, float)) and val >= rule["min"]:
                hit = True
            if hit:
                score += rule["weight"]
                reasons.append(rule["reason"])

    if profile.region_preference and row["region"] in (profile.region_preference, "Pan-India"):
        score += 5
        if row["region"] == profile.region_preference:
            reasons.append(f"matches your {profile.region_preference} regional preference")

    if row["recipe_id"] in profile.liked_recipes:
        score += 12
        reasons.append("similar to dishes you've liked before")
    if row["recipe_id"] in profile.disliked_recipes:
        score -= 25

    if row.get("nutrition_confidence") == "medium":
        score -= 2

    return score, reasons


def recommend(profile: RecommendationProfile, meal_type: str, top_n: int = 5) -> list[dict]:
    df = RecipeStore.get()
    candidates = df[df["meal_type"].str.contains(meal_type, case=False, na=False)].copy()

    # HARD FILTERS
    candidates = candidates[~candidates["is_bulk_recipe"] & ~candidates["is_long_prep"]]
    candidates = candidates[candidates["nutrition_confidence"] != "low"]

    for allergy in profile.allergies:
        col = ALLERGEN_COLS.get(allergy)
        if col:
            candidates = candidates[~candidates[col]]

    if profile.diet_type == "vegetarian":
        candidates = candidates[candidates["diet_type"].isin(["vegetarian", "unknown"])]
        candidates = candidates[~candidates["contains_egg"]]
    elif profile.diet_type == "vegan":
        candidates = candidates[candidates["diet_type"] == "vegan"]
    elif profile.diet_type == "eggetarian":
        candidates = candidates[candidates["diet_type"].isin(["vegetarian", "eggetarian", "unknown"])]

    if profile.max_cooking_time:
        candidates = candidates[candidates["estimated_cooking_time_mins"] <= profile.max_cooking_time]

    candidates = candidates[~candidates["recipe_id"].isin(profile.disliked_recipes)]

    if candidates.empty:
        return []

    meal_target = compute_meal_calorie_target(profile.daily_calorie_target, meal_type)
    scored = []
    for _, row in candidates.iterrows():
        score, reasons = _score_recipe(row, profile, meal_target)
        scored.append({
            "recipe_id": int(row["recipe_id"]),
            "recipe_name": row["recipe_name"],
            "region": row["region"],
            "calories": float(row["calories"]),
            "protein_g": float(row["protein_g"]),
            "cooking_time_mins": float(row["estimated_cooking_time_mins"]),
            "score": round(score, 1),
            "why": ", ".join(reasons) if reasons else "fits your general profile",
            "meal_calorie_target": meal_target,
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_n]
