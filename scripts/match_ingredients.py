"""
NutriCare AI — Phase 2b: ingredient normalization + fuzzy matching against
IFCT (spec sections 14 + 13.C).

For each recipe's ingredient list: split into individual ingredient
phrases, normalize each to a canonical name, estimate its quantity in
grams, then fuzzy-match the normalized name against IFCT's 542 food
entries. Every match is stored with a confidence score — nothing is
accepted blindly (spec section 14).
"""

import pandas as pd
from rapidfuzz import process, fuzz
from normalize_ingredients import normalize_ingredient_phrase, split_ingredient_list

RECIPES_PATH = "../data/processed/recipes_classified.csv"
FOOD_COMP_PATH = "../data/final/food_composition.csv"
OUT_PATH = "../data/final/recipe_ingredients.csv"

HIGH_CONF_THRESHOLD = 85
MEDIUM_CONF_THRESHOLD = 65


def main():
    recipes = pd.read_csv(RECIPES_PATH)
    food_comp = pd.read_csv(FOOD_COMP_PATH)

    # matching choices: lowercase IFCT food names -> food_id
    food_names = food_comp["food_name"].str.lower().tolist()
    name_to_id = dict(zip(food_names, food_comp["food_id"]))

    match_cache: dict[str, tuple] = {}  # normalized_name -> (matched_name, score, food_id)

    def match_name(normalized_name: str):
        if not normalized_name:
            return None, 0.0, None
        if normalized_name in match_cache:
            return match_cache[normalized_name]
        result = process.extractOne(normalized_name, food_names, scorer=fuzz.WRatio)
        if result is None:
            out = (None, 0.0, None)
        else:
            matched_name, score, _ = result
            out = (matched_name, score, name_to_id[matched_name])
        match_cache[normalized_name] = out
        return out

    rows = []
    for _, recipe in recipes.iterrows():
        phrases = split_ingredient_list(recipe["ingredients_text"])
        for phrase in phrases:
            normalized_name, qty_g, qty_flagged = normalize_ingredient_phrase(phrase)
            matched_name, score, food_id = match_name(normalized_name)

            if score >= MEDIUM_CONF_THRESHOLD:
                confidence = round(score / 100, 2)
            else:
                confidence = 0.0  # treated as unresolved
                food_id = None

            rows.append({
                "recipe_id": recipe["recipe_id"],
                "ingredient_raw": phrase,
                "normalized_ingredient_name": normalized_name,
                "quantity_g": round(qty_g, 1),
                "quantity_flagged": qty_flagged,
                "matched_food_id": food_id,
                "matched_food_name": matched_name if confidence > 0 else None,
                "matching_confidence": confidence,
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_PATH, index=False)

    print(f"Saved {len(out)} ingredient rows -> {OUT_PATH}")
    print(f"\nUnique normalized ingredient strings: {len(match_cache)}")

    total = len(out)
    high = (out["matching_confidence"] >= HIGH_CONF_THRESHOLD / 100).sum()
    medium = ((out["matching_confidence"] >= MEDIUM_CONF_THRESHOLD / 100) & (out["matching_confidence"] < HIGH_CONF_THRESHOLD / 100)).sum()
    unresolved = (out["matching_confidence"] == 0).sum()
    print(f"\nMatch quality:")
    print(f"  High confidence   (>={HIGH_CONF_THRESHOLD}%): {high} ({high/total:.1%})")
    print(f"  Medium confidence ({MEDIUM_CONF_THRESHOLD}-{HIGH_CONF_THRESHOLD}%): {medium} ({medium/total:.1%})")
    print(f"  Unresolved        (<{MEDIUM_CONF_THRESHOLD}%): {unresolved} ({unresolved/total:.1%})")

    print("\nSample of unresolved ingredient names (for synonym-map review):")
    unresolved_names = out.loc[out["matching_confidence"] == 0, "normalized_ingredient_name"]
    print(unresolved_names.value_counts().head(25))


if __name__ == "__main__":
    main()
