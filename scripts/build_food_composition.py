"""
NutriCare AI — build food_composition.csv (spec section 13.A) from raw IFCT.

Unit conversions applied here (confirmed by inspecting raw value ranges):
  - enerc (energy) is in kJ  -> convert to kcal (÷ 4.184)
  - na (sodium) and k (potassium) are in grams -> convert to mg (× 1000)
  - protcnt, fatce, cho, fibtg, fsugar are already g / 100g
"""

import pandas as pd

RAW_PATH = "../data/raw/ifct/index.csv"
OUT_PATH = "../data/final/food_composition.csv"


def main():
    df = pd.read_csv(RAW_PATH)

    out = pd.DataFrame({
        "food_id": df["code"],
        "food_name": df["name"],
        "food_group": df["grup"],
        "energy_kcal": (df["enerc"] / 4.184).round(1),
        "protein_g": df["protcnt"],
        "carbohydrate_g": df["cho"],
        "fat_g": df["fatce"],
        "fiber_g": df["fibtg"],
        "sugar_g": df["fsugar"],
        "sodium_mg": (df["na"] * 1000).round(1),
        "source": "IFCT2017",
    })

    # IFCT's 542-item raw-ingredient table has no entries for "salt" or
    # "water" (they're not "foods" in a composition-table sense), but both
    # appear in nearly every recipe's ingredient list, and salt is often
    # the single largest sodium contributor in a dish — dropping it would
    # quietly break the hypertension sodium filter. Values below are
    # standard nutrition-reference constants (not fabricated): table salt
    # is ~38,758mg sodium per 100g (USDA); water contributes 0 of every
    # macro. Sourced separately from IFCT2017 and marked as such.
    supplementary = pd.DataFrame([
        {"food_id": "SUP001", "food_name": "Salt", "food_group": "Supplementary Reference",
         "energy_kcal": 0, "protein_g": 0, "carbohydrate_g": 0, "fat_g": 0,
         "fiber_g": 0, "sugar_g": 0, "sodium_mg": 38758.0, "source": "USDA reference (not IFCT2017)"},
        {"food_id": "SUP002", "food_name": "Water", "food_group": "Supplementary Reference",
         "energy_kcal": 0, "protein_g": 0, "carbohydrate_g": 0, "fat_g": 0,
         "fiber_g": 0, "sugar_g": 0, "sodium_mg": 0, "source": "USDA reference (not IFCT2017)"},
    ])
    out = pd.concat([out, supplementary], ignore_index=True)

    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out)} food composition rows (incl. 2 supplementary reference entries) -> {OUT_PATH}")
    print(out.describe().round(1))


if __name__ == "__main__":
    main()
