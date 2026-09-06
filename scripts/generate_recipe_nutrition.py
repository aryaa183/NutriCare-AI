"""
NutriCare AI — Phase 2c: aggregate recipe_ingredients.csv into per-recipe
nutrition (spec section 13.D).

For each recipe: sum (quantity_g / 100 * nutrient_per_100g) across matched
ingredients (confidence > 0), then divide by servings to get per-serving
values. nutrition_confidence reflects how much of the recipe's ingredient
list (by count) was actually resolved — recipes with poor coverage are
marked accordingly rather than presented as equally reliable.
"""

import pandas as pd

INGREDIENTS_PATH = "../data/final/recipe_ingredients.csv"
FOOD_COMP_PATH = "../data/final/food_composition.csv"
RECIPES_PATH = "../data/processed/recipes_classified.csv"
OUT_PATH = "../data/final/recipe_nutrition.csv"

NUTRIENT_COLS = ["energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]


def main():
    ing = pd.read_csv(INGREDIENTS_PATH)
    food_comp = pd.read_csv(FOOD_COMP_PATH).set_index("food_id")
    recipes = pd.read_csv(RECIPES_PATH)[["recipe_id", "servings"]]

    matched = ing[ing["matched_food_id"].notna()].copy()
    matched = matched.merge(food_comp[NUTRIENT_COLS], left_on="matched_food_id", right_index=True, how="left")

    # scale each ingredient's per-100g nutrients by its estimated quantity
    for col in NUTRIENT_COLS:
        matched[col] = matched[col] * matched["quantity_g"] / 100

    agg = matched.groupby("recipe_id")[NUTRIENT_COLS].sum().reset_index()

    # coverage: fraction of ingredient lines resolved, per recipe
    total_lines = ing.groupby("recipe_id").size().rename("total_ingredients")
    matched_lines = matched.groupby("recipe_id").size().rename("matched_ingredients")
    coverage = pd.concat([total_lines, matched_lines], axis=1).fillna(0)
    coverage["ingredient_coverage"] = (coverage["matched_ingredients"] / coverage["total_ingredients"]).round(2)

    out = agg.merge(coverage.reset_index()[["recipe_id", "ingredient_coverage"]], on="recipe_id", how="left")
    out = out.merge(recipes, on="recipe_id", how="left")

    # scale to per-serving (guard against servings=0 or absurd bulk values)
    safe_servings = out["servings"].clip(lower=1)
    for col in NUTRIENT_COLS:
        out[col] = (out[col] / safe_servings).round(1)

    # confidence tiering — explicit, not hidden in a float nobody reads
    def confidence_tier(cov):
        if cov >= 0.75:
            return "high"
        elif cov >= 0.4:
            return "medium"
        return "low"

    out["nutrition_confidence"] = out["ingredient_coverage"].apply(confidence_tier)

    # Sanity check on the FINAL per-serving number, independent of how we
    # got there. A single home-serving of Indian food realistically falls
    # in ~20-1200 kcal; anything outside that band gets downgraded to
    # "low" confidence and flagged for review rather than shown as
    # equally trustworthy — per-ingredient corrections upstream reduce
    # but don't eliminate the chance of a bad result slipping through
    # (e.g. multiple compounding unit-parsing approximations).
    out["plausibility_flag"] = ~out["energy_kcal"].between(20, 1200)
    out.loc[out["plausibility_flag"], "nutrition_confidence"] = "low"

    out["source"] = "IFCT2017 (matched via ingredient normalization)"

    out = out[["recipe_id", "energy_kcal", "protein_g", "carbohydrate_g", "fat_g",
               "fiber_g", "sugar_g", "sodium_mg", "ingredient_coverage",
               "nutrition_confidence", "plausibility_flag", "source"]]
    out.rename(columns={"energy_kcal": "calories", "carbohydrate_g": "carbs_g"}, inplace=True)

    out.to_csv(OUT_PATH, index=False)
    print(f"Saved nutrition for {len(out)} recipes -> {OUT_PATH}")
    print(f"\nRecipes with NO resolved ingredients at all: {(out['ingredient_coverage']==0).sum()}")
    print(f"Recipes flagged implausible (<20 or >1200 kcal/serving): {out['plausibility_flag'].sum()}")
    print("\nConfidence tier distribution:")
    print(out["nutrition_confidence"].value_counts())
    print("\nSample rows:")
    print(out.sample(5, random_state=1).to_string(index=False))


if __name__ == "__main__":
    main()
