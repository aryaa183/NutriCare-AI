// Types mirror the FastAPI pydantic schemas exactly (app/schemas/*.py) so the
// frontend never guesses a field name — see backend/app/schemas for source of truth.

export type MealType = "Breakfast" | "Lunch" | "Snack" | "Dinner";
export type DietType = "vegetarian" | "non_vegetarian" | "eggetarian" | "vegan";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active";
export type Goal = "weight_loss" | "weight_gain" | "general";
export type Gender = "male" | "female";
export type Condition = "diabetes" | "hypertension" | "heart_disease";
export type BudgetLevel = "low" | "medium" | "flexible";
export type AllergyType =
  | "peanut"
  | "dairy"
  | "egg"
  | "gluten"
  | "soy"
  | "tree_nut"
  | "fish"
  | "shellfish"
  | "sesame"
  | "mustard";

// ---- Auth ----
export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  name: string;
  email: string;
}

// ---- Health profile ----
export interface HealthProfileRequest {
  age: number;
  gender: Gender;
  height_cm: number;
  weight_kg: number;
  activity_level: ActivityLevel;
  goal: Goal;
  diet_type: DietType;
  regional_preference?: string | null;
  budget_level?: BudgetLevel | null;
  max_cooking_time?: number | null;
  allergies: AllergyType[];
  conditions: Condition[];
}

export interface NutritionTargets {
  daily_calorie_target: number;
  protein_target_g: number;
  carb_target_g: number;
  fat_target_g: number;
  fiber_target_g: number;
}

export interface HealthProfileResponse extends HealthProfileRequest {
  nutrition_targets: NutritionTargets;
}

// ---- Recommendations / feedback / meals ----
export interface RecommendationItem {
  recipe_id: number;
  recipe_name: string;
  region: string;
  calories: number;
  protein_g: number;
  cooking_time_mins: number;
  score: number;
  why: string;
  meal_calorie_target: number;
}

export type RecommendationsToday = Record<MealType, RecommendationItem[]>;

export interface FeedbackRequest {
  recipe_id: number;
  interaction_type: "like" | "dislike";
  rating?: number | null;
}

export interface MealLogRequest {
  recipe_id: number;
  meal_type: MealType;
  consumed?: boolean;
}

export interface MealLogHistoryItem {
  recipe_id: number;
  meal_type: MealType;
  consumed: boolean;
  consumed_at: string;
}

export interface RecipeSummary {
  recipe_id: number;
  recipe_name: string;
  meal_type: string;
  region: string;
  diet_type: string;
  calories: number;
  protein_g: number;
}

// Full recipe row — the backend returns the whole CSV row as a dict, so this
// is intentionally loose beyond the fields we know the UI will read.
export interface RecipeDetail extends RecipeSummary {
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  estimated_cooking_time_mins?: number;
  servings?: number;
  nutrition_confidence?: "high" | "medium" | "low";
  source_url?: string;
  [key: string]: unknown;
}

export interface DashboardMealEntry {
  meal_type: string;
  recipe_name: string;
  calories: number;
  protein_g: number;
}

export interface DashboardResponse {
  daily_calorie_target: number;
  calories_consumed: number;
  calories_remaining: number;
  protein_target_g: number;
  protein_consumed_g: number;
  protein_remaining_g: number;
  meals_today: DashboardMealEntry[];
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[];
}
