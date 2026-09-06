import os

class Settings:
    # Defaults to local SQLite for dev/demo; set DATABASE_URL for Postgres
    # in production, e.g. postgresql://user:pass@host:5432/nutricare
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nutricare.db")

    # MUST be overridden via env var in any real deployment — this default
    # exists only so the app runs out-of-the-box for local dev/demo.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RECIPES_CSV_PATH: str = os.getenv(
        "RECIPES_CSV_PATH", "../data/final/nutricare_recipes.csv"
    )


settings = Settings()
