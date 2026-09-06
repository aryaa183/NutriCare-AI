"""
NutriCare AI — Phase 2a: Cuisine filtering + Region / Meal-type / Diet classification.

Deliberately separate from ingredient normalization/matching (Phase 2b) since
this step is cheap, needs no fuzzy matching, and tells us how much usable
Indian-recipe data we actually have before investing in the harder step.

Per spec section 16: do not blindly trust dataset categories — Course/Diet/
Cuisine values here are noisy (some Course values leaked into Cuisine, and
vice versa for Diet), so mappings are explicit and any unmapped value falls
back to keyword rules or an 'unknown' bucket rather than being guessed.
"""

import pandas as pd
import re

RAW_PATH = "../data/raw/recipes/IndianFoodDatasetCSV.csv"
OUT_PATH = "../data/processed/recipes_classified.csv"

# ---------------------------------------------------------------------
# 1. Cuisine -> Region map. Only cuisines in this map are treated as
#    "Indian" and kept. Everything else (Continental, Italian, Thai,
#    stray leaked Course values like "Snack"/"Dessert" appearing in the
#    Cuisine column, etc.) is dropped.
# ---------------------------------------------------------------------
CUISINE_REGION_MAP = {
    # Pan-India / ambiguous but Indian
    "Indian": "Pan-India",
    "Fusion": "Pan-India",
    "Indo Chinese": "Pan-India",

    # North
    "North Indian Recipes": "North", "Punjabi": "North", "Rajasthani": "North",
    "Kashmiri": "North", "Awadhi": "North", "Mughlai": "North",
    "Himachal": "North", "Uttar Pradesh": "North", "Lucknowi": "North",
    "Haryana": "North", "Uttarakhand-North Kumaon": "North", "Sindhi": "North",

    # South
    "South Indian Recipes": "South", "Tamil Nadu": "South", "Karnataka": "South",
    "Andhra": "South", "Chettinad": "South", "Kerala Recipes": "South",
    "Udupi": "South", "Malabar": "South", "Coorg": "South",
    "Coastal Karnataka": "South", "North Karnataka": "South",
    "South Karnataka": "South", "Hyderabadi": "South", "Mangalorean": "South",
    "Kongunadu": "South",

    # West
    "Maharashtrian Recipes": "West", "Gujarati Recipes\ufeff": "West",
    "Gujarati Recipes": "West", "Goan Recipes": "West", "Konkan": "West",
    "Malvani": "West", "Parsi Recipes": "West",

    # East
    "Bengali Recipes": "East", "Oriya Recipes": "East", "Assamese": "East",
    "North East India Recipes": "East", "Jharkhand": "East",
    "Nagaland": "East", "Bihari": "East",
}

NON_INDIAN_OR_NOISE = {  # explicitly excluded — logged for transparency
    "Continental", "Italian Recipes", "Mexican", "Asian", "Thai", "Chinese",
    "French", "Middle Eastern", "Mediterranean", "European", "Greek",
    "African", "Sri Lankan", "Japanese", "Vietnamese", "Pakistani",
    "Indonesian", "Nepalese", "Cantonese", "American", "Sichuan", "British",
    "Malaysian", "Arab", "Caribbean", "Korean", "Hunan", "Afghan",
    "Shandong", "Jewish", "Burmese", "World Breakfast",
    "Appetizer", "Snack", "Side Dish", "Dessert", "Dinner", "Lunch", "Brunch",  # leaked Course values
}

# ---------------------------------------------------------------------
# 2. Course -> meal_type map. Stored as semicolon-joined string since many
#    Indian dishes legitimately serve two meal slots (dal/sabzi/roti work
#    for Lunch AND Dinner) — recommender.py already matches with
#    str.contains(), so this needs no engine change.
# ---------------------------------------------------------------------
COURSE_MEALTYPE_MAP = {
    "Lunch": "Lunch;Dinner",
    "Dinner": "Lunch;Dinner",
    "Main Course": "Lunch;Dinner",
    "One Pot Dish": "Lunch;Dinner",
    "Side Dish": "Lunch;Dinner",
    "Snack": "Snack",
    "Appetizer": "Snack",
    "South Indian Breakfast": "Breakfast",
    "North Indian Breakfast": "Breakfast",
    "Indian Breakfast": "Breakfast",
    "World Breakfast": "Breakfast",
    "Brunch": "Breakfast",
    "Dessert": None,  # not a core meal slot for v1 — excluded from recommendations
}
# Course values that are actually leaked Diet values — ignore Course here,
# use keyword fallback on the recipe name instead.
COURSE_LEAKED_DIET_VALUES = {
    "Vegetarian", "Vegan", "Non Vegeterian", "Eggetarian",
    "High Protein Vegetarian", "No Onion No Garlic (Sattvic)", "Sugar Free Diet",
}

BREAKFAST_KEYWORDS = ["poha", "upma", "idli", "dosa", "paratha", "uttapam",
                       "cheela", "chilla", "sandwich", "vermicelli", "sevai", "porridge"]
SNACK_KEYWORDS = ["chaat", "cutlet", "pakora", "tikki", "samosa", "bhajiya", "vada"]


CONDIMENT_KEYWORDS = [  # not standalone meals — spice mixes, pickles, powders
    "masala powder", "podi recipe", "chutney powder", "spice mix",
    "seasoning powder", "garam masala", "curry powder", "achar recipe",
    "pickle recipe", "sambar powder", "rasam powder",
]


def classify_meal_type(course: str, recipe_name: str) -> str | None:
    name_lower = str(recipe_name).lower()
    if any(kw in name_lower for kw in CONDIMENT_KEYWORDS):
        return None  # condiment/spice-mix recipe, not a servable meal

    if course in COURSE_MEALTYPE_MAP:
        return COURSE_MEALTYPE_MAP[course]
    # course is leaked-diet-value or something unrecognized -> keyword fallback
    name = str(recipe_name).lower()
    if any(k in name for k in BREAKFAST_KEYWORDS):
        return "Breakfast"
    if any(k in name for k in SNACK_KEYWORDS):
        return "Snack"
    return "Lunch;Dinner"  # safe default for unclassified Indian mains


# ---------------------------------------------------------------------
# 3. Diet -> diet_type + health/allergen-adjacent flags.
#    The raw column conflates dietary category with health tags
#    (e.g. "Diabetic Friendly", "Gluten Free" are VALUES of Diet, not
#    modifiers) — split them out explicitly rather than guessing.
# ---------------------------------------------------------------------
DIET_MAP = {
    "Vegetarian":                 {"diet_type": "vegetarian"},
    "High Protein Vegetarian":    {"diet_type": "vegetarian", "high_protein": True},
    "Non Vegeterian":             {"diet_type": "non_vegetarian"},
    "High Protein Non Vegetarian":{"diet_type": "non_vegetarian", "high_protein": True},
    "Eggetarian":                 {"diet_type": "eggetarian"},
    "Vegan":                      {"diet_type": "vegan"},
    "Diabetic Friendly":          {"diet_type": "unknown", "diabetic_friendly_tag": True},
    "Gluten Free":                {"diet_type": "unknown", "gluten_free_tag": True},
    "Sugar Free Diet":            {"diet_type": "unknown", "sugar_free_tag": True},
    "No Onion No Garlic (Sattvic)": {"diet_type": "vegetarian", "sattvic": True},
}
DIET_FLAG_COLS = ["high_protein", "diabetic_friendly_tag", "gluten_free_tag",
                   "sugar_free_tag", "sattvic"]


def classify_diet(diet_raw: str) -> dict:
    base = {"diet_type": "unknown"}
    base.update({c: False for c in DIET_FLAG_COLS})
    mapped = DIET_MAP.get(diet_raw, {})
    base.update(mapped)
    return base


# ---------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------

def main():
    df = pd.read_csv(RAW_PATH)
    n_start = len(df)
    print(f"Loaded {n_start} raw rows.")

    # drop rows missing ingredients (per inspection: 6 rows)
    df = df.dropna(subset=["Ingredients", "TranslatedIngredients"])
    print(f"After dropping missing-ingredient rows: {len(df)}  (-{n_start - len(df)})")

    # region filter — keep only mapped (Indian) cuisines
    df["region"] = df["Cuisine"].map(CUISINE_REGION_MAP)
    excluded_cuisines = sorted(set(df.loc[df["region"].isna(), "Cuisine"].unique()) - set())
    n_before_region = len(df)
    df = df.dropna(subset=["region"])
    print(f"After cuisine/region filter: {len(df)}  (-{n_before_region - len(df)})")

    # meal type classification
    df["meal_type"] = df.apply(
        lambda r: classify_meal_type(r["Course"], r["TranslatedRecipeName"]), axis=1
    )
    n_before_dessert_drop = len(df)
    df = df.dropna(subset=["meal_type"])  # drops Dessert rows (meal_type=None)
    print(f"After dropping non-meal (Dessert) rows: {len(df)}  (-{n_before_dessert_drop - len(df)})")

    # diet classification
    diet_expanded = df["Diet"].apply(classify_diet).apply(pd.Series)
    df = pd.concat([df.reset_index(drop=True), diet_expanded.reset_index(drop=True)], axis=1)

    # flag (not drop) bulk/outlier recipes so the cooking-time/servings
    # filters in the constraint engine naturally exclude them later
    df["is_bulk_recipe"] = df["Servings"] > 20
    df["is_long_prep"] = df["TotalTimeInMins"] > 180

    # final tidy columns
    out = df.rename(columns={
        "Srno": "recipe_id",
        "TranslatedRecipeName": "recipe_name",
        "TranslatedIngredients": "ingredients_text",
        "Cuisine": "cuisine_raw",
        "PrepTimeInMins": "prep_time_mins",
        "CookTimeInMins": "cook_time_mins",
        "TotalTimeInMins": "total_time_mins",
        "Servings": "servings",
        "Diet": "diet_raw",
        "URL": "source_url",
    })[[
        "recipe_id", "recipe_name", "ingredients_text", "region", "cuisine_raw",
        "meal_type", "diet_type", "diet_raw", "high_protein", "diabetic_friendly_tag",
        "gluten_free_tag", "sugar_free_tag", "sattvic", "prep_time_mins",
        "cook_time_mins", "total_time_mins", "servings", "is_bulk_recipe",
        "is_long_prep", "source_url",
    ]]

    out.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(out)} classified recipes -> {OUT_PATH}")

    print("\n--- Region distribution ---")
    print(out["region"].value_counts())
    print("\n--- Meal type distribution ---")
    print(out["meal_type"].value_counts())
    print("\n--- Diet type distribution ---")
    print(out["diet_type"].value_counts())
    print(f"\n--- Health/diet flags (counts of True) ---")
    for col in DIET_FLAG_COLS:
        print(f"  {col}: {out[col].sum()}")
    print(f"\n--- is_bulk_recipe: {out['is_bulk_recipe'].sum()}   is_long_prep: {out['is_long_prep'].sum()} ---")

    print(f"\n--- Excluded (non-Indian / noise) cuisines, for reference ---")
    print(excluded_cuisines)


if __name__ == "__main__":
    main()
