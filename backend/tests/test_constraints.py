"""
Unit tests for the deterministic hard-constraint filters in
recommendation_service.recommend() — allergies, diet type, meal type,
cooking time. Uses a small synthetic dataset so results are deterministic
and don't depend on the real (larger, messier) recipe catalog.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from app.services.recommendation_service import recommend, RecommendationProfile, RecipeStore

SYNTHETIC_RECIPES = pd.DataFrame([
    {"recipe_id": 1, "recipe_name": "Peanut Chutney", "meal_type": "Breakfast", "region": "South",
     "diet_type": "vegetarian", "calories": 150, "protein_g": 5, "carbs_g": 10, "fat_g": 8,
     "fiber_g": 3, "sugar_g": 1, "sodium_mg": 200, "contains_peanut": True, "contains_dairy": False,
     "contains_egg": False, "contains_gluten": False, "contains_soy": False, "contains_tree_nut": False,
     "contains_fish": False, "contains_shellfish": False, "contains_sesame": False, "contains_mustard": False,
     "diabetic_friendly_tag": False, "estimated_cooking_time_mins": 10, "is_bulk_recipe": False,
     "is_long_prep": False, "nutrition_confidence": "high"},
    {"recipe_id": 2, "recipe_name": "Moong Dal Cheela", "meal_type": "Breakfast", "region": "North",
     "diet_type": "vegetarian", "calories": 180, "protein_g": 10, "carbs_g": 20, "fat_g": 5,
     "fiber_g": 4, "sugar_g": 2, "sodium_mg": 220, "contains_peanut": False, "contains_dairy": False,
     "contains_egg": False, "contains_gluten": False, "contains_soy": False, "contains_tree_nut": False,
     "contains_fish": False, "contains_shellfish": False, "contains_sesame": False, "contains_mustard": False,
     "diabetic_friendly_tag": True, "estimated_cooking_time_mins": 15, "is_bulk_recipe": False,
     "is_long_prep": False, "nutrition_confidence": "high"},
    {"recipe_id": 3, "recipe_name": "Egg Bhurji", "meal_type": "Breakfast", "region": "Pan-India",
     "diet_type": "eggetarian", "calories": 220, "protein_g": 14, "carbs_g": 4, "fat_g": 16,
     "fiber_g": 1, "sugar_g": 1, "sodium_mg": 280, "contains_peanut": False, "contains_dairy": False,
     "contains_egg": True, "contains_gluten": False, "contains_soy": False, "contains_tree_nut": False,
     "contains_fish": False, "contains_shellfish": False, "contains_sesame": False, "contains_mustard": False,
     "diabetic_friendly_tag": False, "estimated_cooking_time_mins": 10, "is_bulk_recipe": False,
     "is_long_prep": False, "nutrition_confidence": "high"},
    {"recipe_id": 4, "recipe_name": "Slow-Cooked Bulk Pickle", "meal_type": "Breakfast", "region": "West",
     "diet_type": "vegetarian", "calories": 50, "protein_g": 1, "carbs_g": 5, "fat_g": 2,
     "fiber_g": 1, "sugar_g": 1, "sodium_mg": 900, "contains_peanut": False, "contains_dairy": False,
     "contains_egg": False, "contains_gluten": False, "contains_soy": False, "contains_tree_nut": False,
     "contains_fish": False, "contains_shellfish": False, "contains_sesame": False, "contains_mustard": False,
     "diabetic_friendly_tag": False, "estimated_cooking_time_mins": 20, "is_bulk_recipe": True,
     "is_long_prep": True, "nutrition_confidence": "high"},
    {"recipe_id": 5, "recipe_name": "Wheat Paratha", "meal_type": "Lunch;Dinner", "region": "North",
     "diet_type": "vegetarian", "calories": 300, "protein_g": 7, "carbs_g": 45, "fat_g": 12,
     "fiber_g": 3, "sugar_g": 2, "sodium_mg": 350, "contains_peanut": False, "contains_dairy": True,
     "contains_egg": False, "contains_gluten": True, "contains_soy": False, "contains_tree_nut": False,
     "contains_fish": False, "contains_shellfish": False, "contains_sesame": False, "contains_mustard": False,
     "diabetic_friendly_tag": False, "estimated_cooking_time_mins": 30, "is_bulk_recipe": False,
     "is_long_prep": False, "nutrition_confidence": "low"},
])


def setup_module(module):
    RecipeStore._df = SYNTHETIC_RECIPES.copy()


def base_profile(**overrides) -> RecommendationProfile:
    defaults = dict(daily_calorie_target=2000, diet_type="vegetarian", conditions=[], goal="general")
    defaults.update(overrides)
    return RecommendationProfile(**defaults)


def test_peanut_allergy_excludes_peanut_dish():
    profile = base_profile(allergies=["peanut"])
    results = recommend(profile, "Breakfast", top_n=10)
    ids = [r["recipe_id"] for r in results]
    assert 1 not in ids, "Peanut Chutney must never appear for a peanut-allergic user"


def test_vegetarian_diet_excludes_egg_dish():
    profile = base_profile(diet_type="vegetarian")
    results = recommend(profile, "Breakfast", top_n=10)
    ids = [r["recipe_id"] for r in results]
    assert 3 not in ids, "Egg Bhurji must not appear for a strict vegetarian"


def test_eggetarian_diet_includes_egg_and_vegetarian():
    profile = base_profile(diet_type="eggetarian")
    results = recommend(profile, "Breakfast", top_n=10)
    ids = [r["recipe_id"] for r in results]
    assert 3 in ids
    assert 2 in ids


def test_bulk_and_long_prep_recipes_excluded_by_default():
    profile = base_profile(diet_type="vegetarian")
    results = recommend(profile, "Breakfast", top_n=10)
    ids = [r["recipe_id"] for r in results]
    assert 4 not in ids, "Bulk/long-prep recipes should be excluded from default recommendations"


def test_low_confidence_nutrition_excluded():
    profile = base_profile(diet_type="vegetarian")
    results = recommend(profile, "Lunch", top_n=10)
    ids = [r["recipe_id"] for r in results]
    assert 5 not in ids, "Low nutrition-confidence recipes should not be recommended"


def test_meal_type_filter_is_respected():
    profile = base_profile(diet_type="vegetarian")
    results = recommend(profile, "Dinner", top_n=10)
    # Recipe 5 is Lunch;Dinner but low-confidence -> correctly absent;
    # no other recipe in the fixture is tagged Dinner, so result is empty.
    assert results == []


def test_diabetic_condition_prefers_diabetic_friendly_tag():
    profile = base_profile(diet_type="vegetarian", conditions=["diabetes"])
    results = recommend(profile, "Breakfast", top_n=10)
    # Moong Dal Cheela (id=2) is diabetic_friendly_tag=True -> should score
    # higher than untagged options and appear first
    assert results[0]["recipe_id"] == 2
    assert "diabetic-friendly" in results[0]["why"]


def test_liked_recipe_boosts_rank():
    profile_before = base_profile(diet_type="vegetarian")
    before = recommend(profile_before, "Breakfast", top_n=10)
    top_before = before[0]["recipe_id"]

    # like whichever recipe was ranked last, then confirm it moves up
    other_id = before[-1]["recipe_id"]
    profile_after = base_profile(diet_type="vegetarian", liked_recipes=[other_id])
    after = recommend(profile_after, "Breakfast", top_n=10)
    assert after[0]["recipe_id"] == other_id
    assert "liked before" in after[0]["why"]
