"""
NutriCare AI — content-based recommendation engine (spec sections 18-19),
wired to the real nutricare_recipes.csv produced by the data pipeline.

Same hybrid design as the earlier prototype: deterministic hard-constraint
filtering (allergies, diet type, meal type, cooking time) followed by
explainable weighted scoring — not a black box.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional

DATA_PATH = "../data/final/nutricare_recipes.csv"

ALLERGEN_COLS = {
    "peanut": "contains_peanut", "dairy": "contains_dairy", "egg": "contains_egg",
    "gluten": "contains_gluten", "soy": "contains_soy", "tree_nut": "contains_tree_nut",
    "fish": "contains_fish", "shellfish": "contains_shellfish",
    "sesame": "contains_sesame", "mustard": "contains_mustard",
}


@dataclass
class UserProfile:
    age: int
    weight_kg: float
    height_cm: float
    sex: str
    activity_level: str  # sedentary | light | moderate | active
    goal: str  # weight_loss | weight_gain | general
    diet_type: str = "vegetarian"  # vegetarian | non_vegetarian | eggetarian | vegan
    conditions: List[str] = field(default_factory=list)      # diabetes, hypertension, heart_disease
    allergies: List[str] = field(default_factory=list)       # keys from ALLERGEN_COLS
    region_preference: Optional[str] = None
    max_cooking_time: Optional[int] = None                    # minutes
    liked_recipes: List[int] = field(default_factory=list)
    disliked_recipes: List[int] = field(default_factory=list)


ACTIVITY_MULTIPLIERS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
MEAL_CALORIE_SHARE = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}


def compute_bmr(p: UserProfile) -> float:
    if p.sex.lower() == "male":
        return 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age + 5
    return 10 * p.weight_kg + 6.25 * p.height_cm - 5 * p.age - 161


def compute_meal_target_kcal(p: UserProfile, meal_type: str) -> float:
    tdee = compute_bmr(p) * ACTIVITY_MULTIPLIERS.get(p.activity_level, 1.2)
    if p.goal == "weight_loss":
        tdee -= 400
    elif p.goal == "weight_gain":
        tdee += 400
    return round(tdee * MEAL_CALORIE_SHARE.get(meal_type, 0.3))


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


def score_recipe(row: pd.Series, profile: UserProfile, meal_target_kcal: float) -> tuple[float, list[str]]:
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
        score -= 2  # mild nudge away from lower-confidence nutrition data

    return score, reasons


def recommend(df: pd.DataFrame, profile: UserProfile, meal_type: str, top_n: int = 5) -> pd.DataFrame:
    candidates = df[df["meal_type"].str.contains(meal_type, case=False, na=False)].copy()

    # HARD FILTERS — never overridden by scoring
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
    # non_vegetarian: no diet_type filter, everything allowed

    if profile.max_cooking_time:
        candidates = candidates[candidates["estimated_cooking_time_mins"] <= profile.max_cooking_time]

    candidates = candidates[~candidates["recipe_id"].isin(profile.disliked_recipes)]

    if candidates.empty:
        return pd.DataFrame()

    meal_target = compute_meal_target_kcal(profile, meal_type)
    scored = []
    for _, row in candidates.iterrows():
        score, reasons = score_recipe(row, profile, meal_target)
        scored.append({
            "recipe_id": row["recipe_id"],
            "recipe_name": row["recipe_name"],
            "region": row["region"],
            "calories": row["calories"],
            "protein_g": row["protein_g"],
            "cooking_time_mins": row["estimated_cooking_time_mins"],
            "score": round(score, 1),
            "why": ", ".join(reasons) if reasons else "fits your general profile",
            "meal_calorie_target": meal_target,
        })

    return pd.DataFrame(scored).sort_values("score", ascending=False).head(top_n).reset_index(drop=True)


if __name__ == "__main__":
    df = pd.read_csv(DATA_PATH)
    pd.set_option("display.max_colwidth", 90)
    pd.set_option("display.width", 160)

    print("=" * 80)
    print("CASE 1: Vegetarian, diabetic, hypertension, South Indian, lunch, <=45 min")
    print("=" * 80)
    p1 = UserProfile(age=45, weight_kg=78, height_cm=165, sex="female",
                      activity_level="light", goal="general", diet_type="vegetarian",
                      conditions=["diabetes", "hypertension"], allergies=["dairy"],
                      region_preference="South", max_cooking_time=45)
    print(recommend(df, p1, "Lunch").to_string(index=False))

    print("\n" + "=" * 80)
    print("CASE 2: Non-veg, weight-loss, peanut allergy, dinner")
    print("=" * 80)
    p2 = UserProfile(age=28, weight_kg=85, height_cm=175, sex="male",
                      activity_level="moderate", goal="weight_loss", diet_type="non_vegetarian",
                      allergies=["peanut"])
    print(recommend(df, p2, "Dinner").to_string(index=False))

    print("\n" + "=" * 80)
    print("CASE 3: Vegan, breakfast, gluten allergy")
    print("=" * 80)
    p3 = UserProfile(age=24, weight_kg=60, height_cm=160, sex="female",
                      activity_level="sedentary", goal="general", diet_type="vegan",
                      allergies=["gluten"])
    print(recommend(df, p3, "Breakfast").to_string(index=False))
