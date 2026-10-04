from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.db import models
from app.ml.ranking_model import RankingModel, MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE
from app.ml.train_ranking_model import train_and_save

router = APIRouter(prefix="/ml", tags=["ml"])

@router.get("/status")
def ml_status():
    meta = RankingModel.metadata()
    confidence = RankingModel.confidence()
    return {
        "ml_reranking_active": RankingModel.is_available() and confidence > 0,
        "confidence": round(confidence, 2),
        "n_real_feedback_samples": meta.get("n_real_samples", 0),
        "n_synthetic_bootstrap_samples": meta.get("n_synthetic_samples", 0),
        "min_real_samples_for_full_confidence": MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE,
        "trained_at": meta.get("trained_at"),
        "eval_metrics": meta.get("eval_metrics"),
    }

@router.post("/retrain")
def ml_retrain(current_user: models.User = Depends(get_current_user)):
    metadata = train_and_save()
    return {"detail": "Ranking model retrained", **metadata, "confidence": round(RankingModel.confidence(), 2)}
