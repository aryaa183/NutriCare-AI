import { api } from "./client";
import type {
  DashboardResponse,
  FeedbackRequest,
  HealthProfileRequest,
  HealthProfileResponse,
  LoginRequest,
  MealLogHistoryItem,
  MealLogRequest,
  MealType,
  RecipeDetail,
  RecipeSummary,
  RecommendationItem,
  RecommendationsToday,
  SignupRequest,
  TokenResponse,
  UserResponse,
} from "./types";

// ---- Auth ----
export const signup = (payload: SignupRequest) =>
  api.post<UserResponse>("/auth/signup", payload).then((r) => r.data);

export const login = (payload: LoginRequest) =>
  api.post<TokenResponse>("/auth/login", payload).then((r) => r.data);

export const logout = () => api.post("/auth/logout").then((r) => r.data);

// ---- Profile ----
export const getProfile = () => api.get<HealthProfileResponse>("/profile").then((r) => r.data);

export const createProfile = (payload: HealthProfileRequest) =>
  api.post<HealthProfileResponse>("/profile", payload).then((r) => r.data);

export const updateProfile = (payload: HealthProfileRequest) =>
  api.put<HealthProfileResponse>("/profile", payload).then((r) => r.data);

// ---- Recommendations ----
export const getRecommendationsToday = () =>
  api.get<RecommendationsToday>("/recommendations/today").then((r) => r.data);

export const getRecommendationsForMeal = (mealType: MealType, topN = 5) =>
  api
    .get<RecommendationItem[]>(`/recommendations/${mealType}`, { params: { top_n: topN } })
    .then((r) => r.data);

// ---- Feedback ----
export const submitFeedback = (payload: FeedbackRequest) =>
  api.post("/feedback", payload).then((r) => r.data);

// ---- Recipes ----
export const listRecipes = (params?: {
  meal_type?: string;
  region?: string;
  diet_type?: string;
  limit?: number;
}) => api.get<RecipeSummary[]>("/recipes", { params }).then((r) => r.data);

export const searchRecipes = (q: string, limit = 20) =>
  api.get<RecipeSummary[]>("/recipes/search", { params: { q, limit } }).then((r) => r.data);

export const getRecipe = (recipeId: number) =>
  api.get<RecipeDetail>(`/recipes/${recipeId}`).then((r) => r.data);

// ---- Meals ----
export const logMeal = (payload: MealLogRequest) =>
  api.post("/meals/log", payload).then((r) => r.data);

export const getMealHistory = (limit = 50) =>
  api.get<MealLogHistoryItem[]>("/meals/history", { params: { limit } }).then((r) => r.data);

// ---- Dashboard ----
export const getDashboard = () => api.get<DashboardResponse>("/dashboard").then((r) => r.data);
