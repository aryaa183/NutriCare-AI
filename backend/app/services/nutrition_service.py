"""
Nutrition Calculation Service (spec sections 9-10).
Mifflin-St Jeor BMR, activity-scaled TDEE, goal-based calorie adjustment,
and macro targets derived from standard, citable nutrition guidelines
(not arbitrary numbers):
  - Protein: 1.0 g/kg (general) to 1.6 g/kg (weight_loss/weight_gain,
    to support satiety / muscle retention respectively) — within the
    commonly cited 0.8-2.0 g/kg range for healthy adults.
  - Fat: ~27% of total calories (within the 20-35% AMDR range).
  - Carbohydrate: remainder of calories after protein + fat.
  - Fiber: 14g per 1000 kcal (Institute of Medicine guideline).

Validation guards against unsafe extremes per spec section 9's warning
not to generate unsafe/extreme calorie recommendations.
"""

ACTIVITY_MULTIPLIERS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
MEAL_CALORIE_SHARE = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}

MIN_SAFE_CALORIES = 1200  # floor — never recommend below this regardless of deficit math
MAX_CALORIE_ADJUSTMENT = 500  # cap on deficit/surplus magnitude


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def compute_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender == "male" else base - 161


def compute_daily_targets(weight_kg: float, height_cm: float, age: int, gender: str,
                           activity_level: str, goal: str) -> dict:
    bmr = compute_bmr(weight_kg, height_cm, age, gender)
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)

    adjustment = 0
    if goal == "weight_loss":
        adjustment = -min(MAX_CALORIE_ADJUSTMENT, max(0, tdee - MIN_SAFE_CALORIES))
    elif goal == "weight_gain":
        adjustment = MAX_CALORIE_ADJUSTMENT

    daily_calories = max(MIN_SAFE_CALORIES, round(tdee + adjustment))

    protein_g_per_kg = 1.6 if goal in ("weight_loss", "weight_gain") else 1.0
    protein_g = round(weight_kg * protein_g_per_kg)
    fat_g = round(daily_calories * 0.27 / 9)
    protein_and_fat_kcal = protein_g * 4 + fat_g * 9
    carb_g = max(0, round((daily_calories - protein_and_fat_kcal) / 4))
    fiber_g = round(daily_calories / 1000 * 14)

    return {
        "bmi": compute_bmi(weight_kg, height_cm),
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calorie_target": daily_calories,
        "protein_target_g": protein_g,
        "carb_target_g": carb_g,
        "fat_target_g": fat_g,
        "fiber_target_g": fiber_g,
    }


def compute_meal_calorie_target(daily_calorie_target: float, meal_type: str) -> float:
    return round(daily_calorie_target * MEAL_CALORIE_SHARE.get(meal_type, 0.3))
