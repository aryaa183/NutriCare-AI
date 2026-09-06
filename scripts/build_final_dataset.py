"""
NutriCare AI — Phase 2d: build the final recommendation dataset
(spec section 13.E) by merging classified recipes + aggregated nutrition
+ ingredient-text-based allergen detection.
"""

import pandas as pd
import json
import re

RECIPES_PATH = "../data/processed/recipes_classified.csv"
NUTRITION_PATH = "../data/final/recipe_nutrition.csv"
ALLERGEN_RULES_PATH = "../data/final/allergen_rules.json"
OUT_PATH = "../data/final/nutricare_recipes.csv"


def detect_allergens(ingredients_text: str, rules: dict) -> dict:
    text = str(ingredients_text).lower()
    result = {}
    for allergen, keywords in rules.items():
        result[f"contains_{allergen}"] = any(
            re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords
        )
    return result


def main():
    recipes = pd.read_csv(RECIPES_PATH)
    nutrition = pd.read_csv(NUTRITION_PATH)
    with open(ALLERGEN_RULES_PATH) as f:
        allergen_rules = json.load(f)

    df = recipes.merge(nutrition, on="recipe_id", how="inner")  # inner: only recipes we could compute nutrition for
    print(f"Recipes with both classification and nutrition: {len(df)} (of {len(recipes)} classified)")

    allergen_flags = df["ingredients_text"].apply(lambda t: detect_allergens(t, allergen_rules)).apply(pd.Series)
    df = pd.concat([df.reset_index(drop=True), allergen_flags.reset_index(drop=True)], axis=1)

    df["estimated_cooking_time_mins"] = df["total_time_mins"]

    final_cols = [
        "recipe_id", "recipe_name", "meal_type", "region", "diet_type",
        "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg",
    ] + [f"contains_{a}" for a in allergen_rules] + [
        "diabetic_friendly_tag", "gluten_free_tag", "sugar_free_tag", "high_protein", "sattvic",
        "estimated_cooking_time_mins", "servings", "is_bulk_recipe", "is_long_prep",
        "ingredient_coverage", "nutrition_confidence", "plausibility_flag", "source_url",
    ]
    out = df[final_cols]
    out.to_csv(OUT_PATH, index=False)

    print(f"\nSaved {len(out)} rows -> {OUT_PATH}")
    print(f"\nAllergen prevalence:")
    for a in allergen_rules:
        col = f"contains_{a}"
        print(f"  {col}: {out[col].sum()} ({out[col].mean():.1%})")

    print(f"\nRecommendation-ready recipes (excluding bulk/long-prep/low-confidence for a v1 default view):")
    clean = out[(~out["is_bulk_recipe"]) & (~out["is_long_prep"]) & (out["nutrition_confidence"] != "low")]
    print(f"  {len(clean)} recipes")


if __name__ == "__main__":
    main()
