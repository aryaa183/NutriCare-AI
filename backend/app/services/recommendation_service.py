from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
from app.core.config import settings
from app.services.nutrition_service import compute_meal_calorie_target
from app.services.scoring_rules import ALLERGEN_COLS, score_recipe_rules
from app.ml.features import build_feature_vector
from app.ml.ranking_model import RankingModel

ML_BOOST_SCALE = 20

@dataclass
class RecommendationProfile:
    daily_calorie_target: float
    diet_type: str = "vegetarian"
    conditions: List[str] = field(default_factory=list)
    goal: str = "general"
    allergies: List[str] = field(default_factory=list)
    region_preference: Optional[str] = None
    max_cooking_time: Optional[int] = None
    liked_recipes: List[int] = field(default_factory=list)
    disliked_recipes: List[int] = field(default_factory=list)

class RecipeStore:
    _df: Optional[pd.DataFrame] = None
    @classmethod
    def get(cls) -> pd.DataFrame:
        if cls._df is None: cls._df = pd.read_csv(settings.RECIPES_CSV_PATH)
        return cls._df
    @classmethod
    def reload(cls): cls._df = pd.read_csv(settings.RECIPES_CSV_PATH)

def recommend(profile: RecommendationProfile, meal_type: str, top_n: int = 5) -> list[dict]:
    df=RecipeStore.get()
    candidates=df[df["meal_type"].str.contains(meal_type,case=False,na=False)].copy()
    candidates=candidates[~candidates["is_bulk_recipe"] & ~candidates["is_long_prep"]]
    candidates=candidates[candidates["nutrition_confidence"]!="low"]
    for allergy in profile.allergies:
        col=ALLERGEN_COLS.get(allergy)
        if col: candidates=candidates[~candidates[col]]
    if profile.diet_type=="vegetarian":
        candidates=candidates[candidates["diet_type"].isin(["vegetarian","unknown"])]
        candidates=candidates[~candidates["contains_egg"]]
    elif profile.diet_type=="vegan": candidates=candidates[candidates["diet_type"]=="vegan"]
    elif profile.diet_type=="eggetarian": candidates=candidates[candidates["diet_type"].isin(["vegetarian","eggetarian","unknown"])]
    if profile.max_cooking_time: candidates=candidates[candidates["estimated_cooking_time_mins"]<=profile.max_cooking_time]
    candidates=candidates[~candidates["recipe_id"].isin(profile.disliked_recipes)]
    if candidates.empty: return []
    meal_target=compute_meal_calorie_target(profile.daily_calorie_target,meal_type)
    ml_ready=RankingModel.is_available(); ml_confidence=RankingModel.confidence() if ml_ready else 0.0
    scored=[]; feature_rows=[]
    for _,row in candidates.iterrows():
        rule_score,reasons=score_recipe_rules(row,profile,meal_target)
        scored.append({"recipe_id":int(row["recipe_id"]),"recipe_name":row["recipe_name"],"region":row["region"],"calories":float(row["calories"]),"protein_g":float(row["protein_g"]),"cooking_time_mins":float(row["estimated_cooking_time_mins"]),"score":round(rule_score,1),"why":", ".join(reasons) if reasons else "fits your general profile","meal_calorie_target":meal_target})
        if ml_ready and ml_confidence>0: feature_rows.append(build_feature_vector(row,profile,meal_target))
    if ml_ready and ml_confidence>0:
        for item,prob in zip(scored,RankingModel.predict_proba(feature_rows)):
            boost=(prob-.5)*2*ML_BOOST_SCALE*ml_confidence
            item["score"]=round(item["score"]+boost,1)
            if boost>3: item["why"]+=", and favored by patterns in feedback from users like you"
    scored.sort(key=lambda r:r["score"],reverse=True)
    return scored[:top_n]
