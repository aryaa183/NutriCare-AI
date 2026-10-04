import pandas as pd

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
    "hypertension": [{"field": "sodium_mg", "max": 400, "weight": 15, "reason": "low sodium"}],
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
CONDITION_LIST = ["diabetes", "hypertension", "heart_disease"]
GOAL_LIST = ["weight_loss", "weight_gain", "general"]
DIET_LIST = ["vegetarian", "non_vegetarian", "eggetarian", "vegan"]
CONFIDENCE_SCORE = {"high": 1.0, "medium": 0.5, "low": 0.0}

def score_recipe_rules(row: pd.Series, profile, meal_target_kcal: float) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    diff_ratio = abs(row["calories"] - meal_target_kcal) / max(meal_target_kcal, 1)
    score += max(0, 20 - diff_ratio * 20)
    tags = list(profile.conditions) + ([profile.goal] if profile.goal in CONDITION_RULES else [])
    for tag in set(tags):
        for rule in CONDITION_RULES.get(tag, []):
            val = row[rule["field"]]
            hit = False
            if "equals" in rule and val == rule["equals"]: hit = True
            if "max" in rule and isinstance(val, (int, float)) and val <= rule["max"]: hit = True
            if "min" in rule and isinstance(val, (int, float)) and val >= rule["min"]: hit = True
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
    if row["recipe_id"] in profile.disliked_recipes: score -= 25
    if row.get("nutrition_confidence") == "medium": score -= 2
    return score, reasons
