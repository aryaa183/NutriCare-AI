"""
NutriCare AI — Phase 1: Dataset Inspection ONLY.
Per project spec: do not clean, normalize, or merge here. Just understand
what we're working with before writing any pipeline code.
"""

import pandas as pd
import os

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

IFCT_PATH = "../data/raw/ifct/index.csv"
RECIPES_PATH = "../data/raw/recipes/IndianFoodDatasetCSV.csv"


def inspect(path: str, label: str):
    print("\n" + "=" * 80)
    print(f"{label}  ->  {path}")
    print("=" * 80)

    if not os.path.exists(path):
        print(f"[NOT FOUND] Place the file at this path and re-run.")
        return None

    df = pd.read_csv(path)

    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

    print("\nColumns:")
    for col in df.columns:
        print(f"  - {col}")

    print("\nDtypes:")
    print(df.dtypes)

    print("\nFirst 10 rows:")
    print(df.head(10))

    print("\nMissing values per column:")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.sum() > 0 else "  None")

    print(f"\nDuplicate rows: {df.duplicated().sum()}")

    print("\nDescriptive stats (numeric columns):")
    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        print(numeric_df.describe())
    else:
        print("  No numeric columns detected.")

    # Flag likely nutrition-related columns by keyword match — inspection aid only
    nutrition_keywords = ["energy", "kcal", "calor", "protein", "carb", "fat",
                           "fibre", "fiber", "sugar", "sodium", "vitamin", "mineral", "iron", "calcium"]
    likely_nutrition_cols = [c for c in df.columns if any(k in c.lower() for k in nutrition_keywords)]
    print(f"\nLikely nutrition-related columns detected: {likely_nutrition_cols or 'none found'}")

    recipe_keywords = ["ingredient", "cuisine", "course", "diet", "instruction", "prep", "cook", "serv"]
    likely_recipe_cols = [c for c in df.columns if any(k in c.lower() for k in recipe_keywords)]
    print(f"Likely recipe-related columns detected: {likely_recipe_cols or 'none found'}")

    return df


if __name__ == "__main__":
    ifct_df = inspect(IFCT_PATH, "DATASET 1: IFCT 2017 (Food Composition)")
    recipe_df = inspect(RECIPES_PATH, "DATASET 2: Indian Food Recipes")

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE — STOPPING HERE PER PLAN")
    print("=" * 80)
    print("Review the output above before we design the cleaning/matching pipeline.")
