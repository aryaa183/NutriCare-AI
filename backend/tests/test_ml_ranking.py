import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))
import pandas as pd
import pytest
from app.ml.features import build_feature_vector,FEATURE_NAMES
from app.ml.ranking_model import RankingModel,MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE
from app.services.recommendation_service import recommend,RecommendationProfile,RecipeStore
SYNTHETIC_RECIPES=pd.DataFrame([
{"recipe_id":1,"recipe_name":"Moong Dal Cheela","meal_type":"Breakfast","region":"North","diet_type":"vegetarian","calories":180,"protein_g":10,"carbs_g":20,"fat_g":5,"fiber_g":4,"sugar_g":2,"sodium_mg":220,"contains_peanut":False,"contains_dairy":False,"contains_egg":False,"contains_gluten":False,"contains_soy":False,"contains_tree_nut":False,"contains_fish":False,"contains_shellfish":False,"contains_sesame":False,"contains_mustard":False,"diabetic_friendly_tag":True,"estimated_cooking_time_mins":15,"is_bulk_recipe":False,"is_long_prep":False,"nutrition_confidence":"high"},
{"recipe_id":2,"recipe_name":"Veg Upma","meal_type":"Breakfast","region":"South","diet_type":"vegetarian","calories":220,"protein_g":6,"carbs_g":30,"fat_g":7,"fiber_g":3,"sugar_g":2,"sodium_mg":300,"contains_peanut":False,"contains_dairy":False,"contains_egg":False,"contains_gluten":True,"contains_soy":False,"contains_tree_nut":False,"contains_fish":False,"contains_shellfish":False,"contains_sesame":False,"contains_mustard":False,"diabetic_friendly_tag":False,"estimated_cooking_time_mins":20,"is_bulk_recipe":False,"is_long_prep":False,"nutrition_confidence":"high"}])
@pytest.fixture
def profile(): return RecommendationProfile(daily_calorie_target=1800,diet_type="vegetarian",conditions=["diabetes"])
def test_feature_vector_shape(profile):
    f=build_feature_vector(SYNTHETIC_RECIPES.iloc[0],profile,450); assert len(f)==len(FEATURE_NAMES); assert all(isinstance(x,float) for x in f)
def test_feature_vector_deterministic(profile):
    r=SYNTHETIC_RECIPES.iloc[0]; assert build_feature_vector(r,profile,450)==build_feature_vector(r,profile,450)
def test_no_artifact_means_zero_confidence(monkeypatch):
    monkeypatch.setattr(RankingModel,"_pipeline",None); monkeypatch.setattr(RankingModel,"_metadata",None); monkeypatch.setattr(RankingModel,"_loaded_attempted",True)
    assert not RankingModel.is_available() and RankingModel.confidence()==0.0
def test_confidence_scales_with_real_samples(monkeypatch):
    monkeypatch.setattr(RankingModel,"_loaded_attempted",True); monkeypatch.setattr(RankingModel,"_pipeline",object())
    for n,expected in [(0,0.0),(MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE//2,None),(MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE*5,1.0)]:
        monkeypatch.setattr(RankingModel,"_metadata",{"n_real_samples":n})
        c=RankingModel.confidence()
        assert c==expected if expected is not None else 0<c<1
def test_recommend_unaffected_when_ml_has_no_real_signal(monkeypatch,profile):
    RecipeStore._df=SYNTHETIC_RECIPES.copy(); monkeypatch.setattr(RankingModel,"_loaded_attempted",True); monkeypatch.setattr(RankingModel,"_pipeline",object()); monkeypatch.setattr(RankingModel,"_metadata",{"n_real_samples":0})
    results=recommend(profile,"Breakfast",5); assert len(results)==2 and results[0]["recipe_name"]=="Moong Dal Cheela"; RecipeStore._df=None
