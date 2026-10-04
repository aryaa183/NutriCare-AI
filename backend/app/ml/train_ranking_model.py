import random
from datetime import datetime,timezone
import joblib,numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score
from app.core.config import settings
from app.db.database import SessionLocal
from app.db import models
from app.services.nutrition_service import compute_meal_calorie_target
from app.services.scoring_rules import CONDITION_LIST,GOAL_LIST,DIET_LIST
from app.ml.features import build_feature_vector
from app.ml.ranking_model import ARTIFACT_PATH,RankingModel
N_SYNTHETIC_SAMPLES=5000; SYNTHETIC_SAMPLE_WEIGHT=.3; REAL_SAMPLE_WEIGHT=1.; RANDOM_SEED=42
class _SyntheticProfile:
    def __init__(self,conditions,goal,diet_type,region_preference):
        self.conditions=conditions; self.goal=goal; self.diet_type=diet_type; self.region_preference=region_preference; self.liked_recipes=[]; self.disliked_recipes=[]
def _load_recipes(): return pd.read_csv(settings.RECIPES_CSV_PATH)
def _synthetic_training_rows(recipes,rng):
    regions=[r for r in recipes.region.dropna().unique().tolist()]+[None]; X=[];y=[];w=[]
    for _,row in recipes.sample(n=N_SYNTHETIC_SAMPLES,replace=True,random_state=RANDOM_SEED).iterrows():
        p=_SyntheticProfile(rng.sample(CONDITION_LIST,k=rng.randint(0,2)),rng.choice(GOAL_LIST),rng.choice(DIET_LIST),rng.choice(regions))
        target=compute_meal_calorie_target(rng.uniform(1400,2600),rng.choice(["Breakfast","Lunch","Snack","Dinner"]))
        f=build_feature_vector(row,p,target); prob=1/(1+np.exp(-(f[10]-20)/8)); prob=float(np.clip(prob+rng.gauss(0,.12),.02,.98))
        X.append(f);y.append(1 if rng.random()<prob else 0);w.append(SYNTHETIC_SAMPLE_WEIGHT)
    return X,y,w
def _real_training_rows(recipes):
    db=SessionLocal(); X=[];y=[];w=[]
    try:
        byid=recipes.set_index("recipe_id",drop=False)
        for fb in db.query(models.UserFeedback).all():
            if fb.recipe_id not in byid.index or fb.user.health_profile is None: continue
            hp=fb.user.health_profile; prefs=fb.user.preferences
            p=_SyntheticProfile([c.condition for c in fb.user.conditions],hp.goal,prefs.diet_type if prefs else "vegetarian",prefs.regional_preference if prefs else None)
            row=byid.loc[fb.recipe_id]; row=row.iloc[0] if isinstance(row,pd.DataFrame) else row
            target=compute_meal_calorie_target(hp.daily_calorie_target,str(row.get("meal_type","Lunch")).split(";")[0])
            X.append(build_feature_vector(row,p,target)); y.append(1 if fb.interaction_type=="like" else 0); w.append(REAL_SAMPLE_WEIGHT)
    finally: db.close()
    return X,y,w
def train_and_save():
    rng=random.Random(RANDOM_SEED); recipes=_load_recipes(); rx,ry,rw=_real_training_rows(recipes); sx,sy,sw=_synthetic_training_rows(recipes,rng)
    X=np.array(rx+sx,float); y=np.array(ry+sy,int); weights=np.array(rw+sw,float)
    Xtr,Xte,ytr,yte,wtr,_=train_test_split(X,y,weights,test_size=.2,random_state=RANDOM_SEED,stratify=y)
    eval_pipe=Pipeline([("scaler",StandardScaler()),("clf",LogisticRegression(max_iter=1000,class_weight="balanced"))]); eval_pipe.fit(Xtr,ytr,clf__sample_weight=wtr)
    yp=eval_pipe.predict(Xte); pp=eval_pipe.predict_proba(Xte)[:,1]
    metrics={"accuracy":float(accuracy_score(yte,yp)),"precision":float(precision_score(yte,yp,zero_division=0)),"recall":float(recall_score(yte,yp,zero_division=0)),"f1":float(f1_score(yte,yp,zero_division=0)),"roc_auc":float(roc_auc_score(yte,pp)),"n_test_samples":len(yte),"evaluated_on":"real+synthetic held-out split" if rx else "synthetic held-out split (no real feedback yet)"}
    pipe=Pipeline([("scaler",StandardScaler()),("clf",LogisticRegression(max_iter=1000,class_weight="balanced"))]); pipe.fit(X,y,clf__sample_weight=weights)
    meta={"n_real_samples":len(rx),"n_synthetic_samples":len(sx),"trained_at":datetime.now(timezone.utc).isoformat(),"eval_metrics":metrics}
    ARTIFACT_PATH.parent.mkdir(parents=True,exist_ok=True); joblib.dump({"pipeline":pipe,"metadata":meta},ARTIFACT_PATH); RankingModel.reload(); return meta
if __name__=="__main__": print(train_and_save())
