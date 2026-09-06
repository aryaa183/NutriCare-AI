from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.database import Base, engine
from app.services.recommendation_service import RecipeStore
from app.api.routers import auth, profile, recommendations, feedback, meals, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: create tables if they don't exist. A real deployment
    # uses Alembic migrations instead (spec section 24) — this is fine for
    # local/demo use where the DB starts empty.
    Base.metadata.create_all(bind=engine)
    RecipeStore.get()  # preload recipe catalog into memory once at startup
    yield


app = FastAPI(
    title="NutriCare AI",
    description="Adaptive personalized Indian food recommendation platform. "
                 "This platform provides general nutrition recommendations and is not a "
                 "substitute for professional medical advice, diagnosis, or treatment.",
    version="0.1.0",
    lifespan=lifespan,
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.get("/")
def root():
    return {
        "service": "NutriCare AI",
        "disclaimer": "This platform provides general nutrition recommendations and is not "
                       "a substitute for professional medical advice, diagnosis, or treatment.",
        "docs": "/docs",
    }
