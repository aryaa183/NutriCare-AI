from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    health_profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    allergies = relationship("UserAllergy", back_populates="user", cascade="all, delete-orphan")
    conditions = relationship("UserHealthCondition", back_populates="user", cascade="all, delete-orphan")
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # "male" | "female"
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)

    activity_level = Column(String, nullable=False)  # sedentary|light|moderate|active
    goal = Column(String, nullable=False)  # weight_loss|weight_gain|general

    daily_calorie_target = Column(Float)
    protein_target_g = Column(Float)
    carb_target_g = Column(Float)
    fat_target_g = Column(Float)
    fiber_target_g = Column(Float)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="health_profile")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    diet_type = Column(String, nullable=False, default="vegetarian")
    regional_preference = Column(String, nullable=True)
    budget_level = Column(String, nullable=True)  # low|medium|flexible
    max_cooking_time = Column(Integer, nullable=True)  # minutes

    user = relationship("User", back_populates="preferences")


class UserAllergy(Base):
    __tablename__ = "user_allergies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    allergy_type = Column(String, nullable=False)  # matches ALLERGEN_COLS keys

    user = relationship("User", back_populates="allergies")


class UserHealthCondition(Base):
    __tablename__ = "user_health_conditions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition = Column(String, nullable=False)  # diabetes|hypertension|heart_disease

    user = relationship("User", back_populates="conditions")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, nullable=False)  # references nutricare_recipes.csv recipe_id (dataset-backed, not FK)
    meal_type = Column(String, nullable=False)
    consumed = Column(Boolean, default=True)
    consumed_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="meal_logs")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, nullable=False)
    interaction_type = Column(String, nullable=False)  # "like" | "dislike"
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="feedback")
