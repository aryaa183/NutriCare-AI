from pathlib import Path
from typing import Optional
import joblib

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "ranking_model.joblib"
MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE = 20

class RankingModel:
    _pipeline = None
    _metadata: Optional[dict] = None
    _loaded_attempted = False
    @classmethod
    def load(cls):
        cls._loaded_attempted = True
        if not ARTIFACT_PATH.exists():
            cls._pipeline, cls._metadata = None, None
            return
        bundle = joblib.load(ARTIFACT_PATH)
        cls._pipeline = bundle["pipeline"]
        cls._metadata = bundle["metadata"]
    @classmethod
    def reload(cls): cls.load()
    @classmethod
    def _ensure_loaded(cls):
        if not cls._loaded_attempted: cls.load()
    @classmethod
    def is_available(cls) -> bool:
        cls._ensure_loaded(); return cls._pipeline is not None
    @classmethod
    def metadata(cls) -> dict:
        cls._ensure_loaded()
        return dict(cls._metadata) if cls._metadata else {"n_real_samples": 0, "n_synthetic_samples": 0, "trained_at": None}
    @classmethod
    def confidence(cls) -> float:
        n_real = cls.metadata().get("n_real_samples", 0)
        return min(1.0, n_real / MIN_REAL_SAMPLES_FOR_FULL_CONFIDENCE)
    @classmethod
    def predict_proba(cls, feature_rows: list[list[float]]) -> list[float]:
        cls._ensure_loaded()
        if cls._pipeline is None or not feature_rows: return [0.5] * len(feature_rows)
        return list(cls._pipeline.predict_proba(feature_rows)[:, 1])
