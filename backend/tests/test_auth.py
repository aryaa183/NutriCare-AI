"""
Auth endpoint tests using FastAPI's TestClient against an isolated
in-memory SQLite DB (dependency-overridden), so these never touch the
dev nutricare.db file or require a running server.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db

TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


client = TestClient(app)


def test_signup_success():
    r = client.post("/auth/signup", json={"name": "Test User", "email": "test1@example.com", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "test1@example.com"
    assert "password" not in body and "password_hash" not in body


def test_signup_duplicate_email_rejected():
    client.post("/auth/signup", json={"name": "A", "email": "dup@example.com", "password": "password123"})
    r = client.post("/auth/signup", json={"name": "B", "email": "dup@example.com", "password": "password456"})
    assert r.status_code == 409


def test_signup_short_password_rejected():
    r = client.post("/auth/signup", json={"name": "A", "email": "short@example.com", "password": "short"})
    assert r.status_code == 422  # Pydantic min_length=8 validation


def test_login_success_returns_tokens():
    client.post("/auth/signup", json={"name": "A", "email": "login@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_wrong_password_rejected():
    client.post("/auth/signup", json={"name": "A", "email": "wrong@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "wrong@example.com", "password": "notthis123"})
    assert r.status_code == 401


def test_login_nonexistent_user_rejected():
    r = client.post("/auth/login", json={"email": "ghost@example.com", "password": "whatever123"})
    assert r.status_code == 401


def test_protected_route_requires_token():
    r = client.get("/profile")
    assert r.status_code in (401, 403)


def test_protected_route_rejects_garbage_token():
    r = client.get("/profile", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_password_is_actually_hashed_not_stored_plaintext():
    from app.db import models
    client.post("/auth/signup", json={"name": "A", "email": "hashcheck@example.com", "password": "password123"})
    db = TestSessionLocal()
    user = db.query(models.User).filter(models.User.email == "hashcheck@example.com").first()
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix
    db.close()
