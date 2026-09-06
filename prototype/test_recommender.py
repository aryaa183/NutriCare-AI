import pandas as pd
from recommender import UserProfile, recommend_meals, record_feedback

df = pd.read_csv("../data/indian_food_sample.csv")

print("=" * 70)
print("CASE 1: Diabetic, South Indian preference, wants lunch")
print("=" * 70)
p1 = UserProfile(
    age=45, weight_kg=78, height_cm=165, sex="female",
    activity_level="light", goal="general",
    conditions=["diabetes"], allergies=["dairy"],
    region_preference="South",
)
print(recommend_meals(df, p1, "Lunch", top_n=3).to_string(index=False))

print()
print("=" * 70)
print("CASE 2: Weight-loss goal, hypertension, nut allergy, dinner")
print("=" * 70)
p2 = UserProfile(
    age=30, weight_kg=90, height_cm=170, sex="male",
    activity_level="moderate", goal="weight_loss",
    conditions=["hypertension"], allergies=["nuts"],
)
print(recommend_meals(df, p2, "Dinner", top_n=3).to_string(index=False))

print()
print("=" * 70)
print("CASE 3: Fasting day snack suggestions")
print("=" * 70)
p3 = UserProfile(
    age=28, weight_kg=60, height_cm=160, sex="female",
    activity_level="sedentary", goal="general",
)
print(recommend_meals(df, p3, "Snack", top_n=3, fasting_mode=True).to_string(index=False))

print()
print("=" * 70)
print("CASE 4: Same profile as Case 1, but after disliking Curd Rice (D019)")
print("=" * 70)
record_feedback(p1, "D019", liked=False)
record_feedback(p1, "D012", liked=True)
print(recommend_meals(df, p1, "Lunch", top_n=3).to_string(index=False))
