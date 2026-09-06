"""Unit tests for nutrition_service — BMI/BMR/TDEE math and safety bounds."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.nutrition_service import compute_bmi, compute_bmr, compute_daily_targets, MIN_SAFE_CALORIES


def test_bmi_known_value():
    # 70kg, 175cm -> BMI = 70 / 1.75^2 = 22.9
    assert compute_bmi(70, 175) == 22.9


def test_bmr_male_vs_female_formula_offset():
    # Same stats, only gender differs -> difference should be exactly 166
    # (Mifflin-St Jeor: +5 for male, -161 for female)
    bmr_male = compute_bmr(70, 175, 30, "male")
    bmr_female = compute_bmr(70, 175, 30, "female")
    assert round(bmr_male - bmr_female) == 166


def test_daily_targets_never_below_safety_floor():
    # A small, sedentary, weight-loss profile should still never drop
    # below MIN_SAFE_CALORIES, regardless of how the deficit math computes
    targets = compute_daily_targets(weight_kg=40, height_cm=145, age=50, gender="female",
                                     activity_level="sedentary", goal="weight_loss")
    assert targets["daily_calorie_target"] >= MIN_SAFE_CALORIES


def test_weight_gain_increases_target_vs_general():
    common = dict(weight_kg=70, height_cm=175, age=25, gender="male", activity_level="moderate")
    general = compute_daily_targets(**common, goal="general")
    gain = compute_daily_targets(**common, goal="weight_gain")
    loss = compute_daily_targets(**common, goal="weight_loss")
    assert gain["daily_calorie_target"] > general["daily_calorie_target"] > loss["daily_calorie_target"]


def test_macro_targets_are_positive_and_consistent():
    targets = compute_daily_targets(weight_kg=78, height_cm=165, age=45, gender="female",
                                     activity_level="light", goal="general")
    for key in ["protein_target_g", "carb_target_g", "fat_target_g", "fiber_target_g"]:
        assert targets[key] > 0
    # protein+fat+carb calories should roughly reconstruct the daily target
    reconstructed = targets["protein_target_g"] * 4 + targets["fat_target_g"] * 9 + targets["carb_target_g"] * 4
    assert abs(reconstructed - targets["daily_calorie_target"]) < 50
