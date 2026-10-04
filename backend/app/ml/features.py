from __future__ import annotations
import pandas as pd
from app.services.scoring_rules import CONDITION_LIST, GOAL_LIST, DIET_LIST, CONFIDENCE_SCORE, score_recipe_rules

FEATURE_NAMES = [
    "calorie_diff_ratio", "protein_g", "fiber_g", "sugar_g", "sodium_mg", "fat_g",
    "cooking_time_mins", "region_match", "diabetic_friendly", "nutrition_confidence", "rule_score",
] + [f"condition_{c}" for c in CONDITION_LIST] + [f"goal_{g}" for g in GOAL_LIST] + [f"diet_{d}" for d in DIET_LIST]

def build_feature_vector(row: pd.Series, profile, meal_target_kcal: float) -> list[float]:
    rule_score, _ = score_recipe_rules(row, profile, meal_target_kcal)
    diff_ratio = abs(row["calories"] - meal_target_kcal) / max(meal_target_kcal, 1)
    region_match = 1.0 if (profile.region_preference and row["region"] in (profile.region_preference, "Pan-India")) else 0.0
    features = [
        min(diff_ratio, 2.0), float(row.get("protein_g", 0) or 0), float(row.get("fiber_g", 0) or 0),
        float(row.get("sugar_g", 0) or 0), float(row.get("sodium_mg", 0) or 0), float(row.get("fat_g", 0) or 0),
        float(row.get("estimated_cooking_time_mins", 0) or 0), region_match,
        1.0 if row.get("diabetic_friendly_tag") else 0.0, CONFIDENCE_SCORE.get(row.get("nutrition_confidence"), 0.5), rule_score,
    ]
    features += [1.0 if c in profile.conditions else 0.0 for c in CONDITION_LIST]
    features += [1.0 if profile.goal == g else 0.0 for g in GOAL_LIST]
    features += [1.0 if profile.diet_type == d else 0.0 for d in DIET_LIST]
    return features
