from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine
from app.services.recommendation_service import RecipeStore
from app.ml.ranking_model import RankingModel
from app.api.routers import auth, profile, recommendations, feedback, meals, dashboard, ml

def _check_production_config():
    if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "dev-only-secret-change-me":
        raise RuntimeError("Refusing to start: ENVIRONMENT=production but SECRET_KEY is still the dev default. Set a real SECRET_KEY env var before deploying.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_config()
    Base.metadata.create_all(bind=engine)
    RecipeStore.get()
    RankingModel.load()
    yield

app = FastAPI(
    title="NutriCare AI",
    description="Adaptive personalized Indian food recommendation platform. This platform provides general nutrition recommendations and is not a substitute for professional medical advice, diagnosis, or treatment.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(feedback.router)
app.include_router(meals.router)
app.include_router(dashboard.router)
app.include_router(ml.router)

@app.get("/")
def root():
    return {
        "service": "NutriCare AI",
        "disclaimer": "This platform provides general nutrition recommendations and is not a substitute for professional medical advice, diagnosis, or treatment.",
        "docs": "/docs",
    }
