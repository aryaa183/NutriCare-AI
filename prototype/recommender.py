"""
Indian Food Recommendation Engine — core logic
Rule-weighted content-based scoring (not a black-box model) so every
recommendation is explainable, plus a lightweight feedback hook for
adaptive re-ranking.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------
# 1. User profile
# ---------------------------------------------------------------------

@dataclass
class UserProfile:
    age: int
    weight_kg: float
    height_cm: float
    sex: str  # "male" / "female"
    activity_level: str  # "sedentary" | "light" | "moderate" | "active"
    goal: str  # "weight_loss" | "weight_gain" | "general"
    conditions: List[str] = field(default_factory=list)   # e.g. ["diabetes", "hypertension"]
    allergies: List[str] = field(default_factory=list)    # e.g. ["dairy", "nuts"]
    region_preference: Optional[str] = None                # e.g. "South"
    disliked_dishes: List[str] = field(default_factory=list)   # dish_ids from feedback
    liked_dishes: List[str] = field(default_factory=list)      # dish_ids from feedback


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

# calorie split per meal (rough Indian meal pattern)
MEAL_CALORIE_SHARE = {
    "Breakfast": 0.25,
    "Lunch": 0.35,
    "Dinner": 0.30,
    "Snack": 0.10,
}


def compute_bmr(profile: UserProfile) -> float:
    """Mifflin-St Jeor equation."""
    if profile.sex.lower() == "male":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161


def compute_daily_calorie_target(profile: UserProfile) -> float:
    bmr = compute_bmr(profile)
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.2)
    if profile.goal == "weight_loss":
        tdee -= 400
    elif profile.goal == "weight_gain":
        tdee += 400
    return round(tdee)


def compute_meal_target(profile: UserProfile, meal_type: str) -> float:
    daily = compute_daily_calorie_target(profile)
    return round(daily * MEAL_CALORIE_SHARE.get(meal_type, 0.3))


# ---------------------------------------------------------------------
# 2. Condition -> nutrient rule weighting (this is the "explainable" layer)
# ---------------------------------------------------------------------

# Each rule: penalty/bonus applied based on a nutrient threshold, plus the
# human-readable reason shown to the user.
CONDITION_RULES = {
    "diabetes": [
        {"field": "gi_category", "prefer": "Low", "weight": 15, "reason": "low glycemic index (better blood sugar control)"},
        {"field": "sugar_g", "max": 5, "weight": 10, "reason": "low sugar content"},
        {"field": "fiber_g", "min": 4, "weight": 8, "reason": "good fiber content"},
    ],
    "hypertension": [
        {"field": "sodium_mg", "max": 300, "weight": 15, "reason": "low sodium"},
    ],
    "heart_disease": [
        {"field": "fat_g", "max": 15, "weight": 10, "reason": "moderate fat content"},
        {"field": "sodium_mg", "max": 350, "weight": 10, "reason": "controlled sodium"},
        {"field": "fiber_g", "min": 4, "weight": 6, "reason": "heart-friendly fiber"},
    ],
    "weight_loss": [
        {"field": "calories_kcal", "max": 280, "weight": 8, "reason": "calorie-light option"},
        {"field": "fiber_g", "min": 4, "weight": 8, "reason": "keeps you fuller for longer"},
    ],
    "weight_gain": [
        {"field": "calories_kcal", "min": 280, "weight": 8, "reason": "calorie-dense option"},
        {"field": "protein_g", "min": 12, "weight": 8, "reason": "good protein for muscle gain"},
    ],
}


def score_dish(row: pd.Series, profile: UserProfile, meal_target_kcal: float) -> tuple[float, list[str]]:
    """Returns (score, list_of_reasons) for a single dish."""
    score = 0.0
    reasons = []

    # base fit: how close is the dish calorie count to the per-meal target
    diff_ratio = abs(row["calories_kcal"] - meal_target_kcal) / meal_target_kcal
    score += max(0, 20 - diff_ratio * 20)

    # condition-driven scoring
    tags_to_check = profile.conditions + ([profile.goal] if profile.goal in CONDITION_RULES else [])
    for tag in set(tags_to_check):
        for rule in CONDITION_RULES.get(tag, []):
            field_name = rule["field"]
            val = row[field_name]
            hit = False
            if "prefer" in rule and val == rule["prefer"]:
                hit = True
            if "max" in rule and isinstance(val, (int, float)) and val <= rule["max"]:
                hit = True
            if "min" in rule and isinstance(val, (int, float)) and val >= rule["min"]:
                hit = True
            if hit:
                score += rule["weight"]
                reasons.append(rule["reason"])

    # region preference bonus (soft, not a hard filter)
    if profile.region_preference and row["region"] in (profile.region_preference, "Pan-India"):
        score += 5
        if row["region"] == profile.region_preference:
            reasons.append(f"matches your {profile.region_preference} regional preference")

    # feedback-based nudge (the adaptive layer)
    if row["dish_id"] in profile.liked_dishes:
        score += 12
        reasons.append("similar to dishes you've liked before")
    if row["dish_id"] in profile.disliked_dishes:
        score -= 25

    return score, reasons


# ---------------------------------------------------------------------
# 3. Main recommendation function
# ---------------------------------------------------------------------

def recommend_meals(
    df: pd.DataFrame,
    profile: UserProfile,
    meal_type: str,
    top_n: int = 3,
    fasting_mode: bool = False,
) -> pd.DataFrame:
    candidates = df[df["meal_type"].str.contains(meal_type, case=False, na=False)].copy()

    # HARD filter 1: allergies — never negotiable
    if profile.allergies:
        def is_safe(allergen_str):
            dish_allergens = set(a.strip() for a in str(allergen_str).split(";"))
            return dish_allergens.isdisjoint(set(profile.allergies))
        candidates = candidates[candidates["allergens"].apply(is_safe)]

    # HARD filter 2: fasting mode
    if fasting_mode:
        candidates = candidates[candidates["fasting_friendly"] == "yes"]

    # HARD filter 3: already disliked dishes get excluded outright if very disliked
    candidates = candidates[~candidates["dish_id"].isin(profile.disliked_dishes)]

    if candidates.empty:
        return pd.DataFrame()

    meal_target = compute_meal_target(profile, meal_type)

    scored_rows = []
    for _, row in candidates.iterrows():
        score, reasons = score_dish(row, profile, meal_target)
        scored_rows.append({
            "dish_id": row["dish_id"],
            "dish_name": row["dish_name"],
            "region": row["region"],
            "calories_kcal": row["calories_kcal"],
            "protein_g": row["protein_g"],
            "score": round(score, 1),
            "why": ", ".join(reasons) if reasons else "fits your general profile",
            "meal_calorie_target": meal_target,
        })

    result = pd.DataFrame(scored_rows).sort_values("score", ascending=False).head(top_n)
    return result.reset_index(drop=True)


# ---------------------------------------------------------------------
# 4. Feedback hook (stub for the adaptive/ML layer)
# ---------------------------------------------------------------------

def record_feedback(profile: UserProfile, dish_id: str, liked: bool):
    """Update the user's like/dislike history. In a real app this writes to
    the DB (Firebase) and the liked/disliked lists get reloaded into the
    profile on next request — this is what turns the system from a static
    rule engine into an adaptive one."""
    if liked:
        if dish_id not in profile.liked_dishes:
            profile.liked_dishes.append(dish_id)
        if dish_id in profile.disliked_dishes:
            profile.disliked_dishes.remove(dish_id)
    else:
        if dish_id not in profile.disliked_dishes:
            profile.disliked_dishes.append(dish_id)
        if dish_id in profile.liked_dishes:
            profile.liked_dishes.remove(dish_id)
