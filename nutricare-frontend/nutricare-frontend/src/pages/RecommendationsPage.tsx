import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { MealType, RecommendationItem } from "../api/types";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { MealTabs } from "../components/MealTabs";
import { RecipeRow } from "../components/RecipeRow";

function defaultMealForHour(hour: number): MealType {
  if (hour < 10) return "Breakfast";
  if (hour < 15) return "Lunch";
  if (hour < 18) return "Snack";
  return "Dinner";
}

export function RecommendationsPage() {
  const [meal, setMeal] = useState<MealType>(() => defaultMealForHour(new Date().getHours()));
  const [items, setItems] = useState<RecommendationItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<Record<number, "like" | "dislike">>({});
  const [logged, setLogged] = useState<Record<number, boolean>>({});
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setItems(null);
    endpoints
      .getRecommendationsForMeal(meal)
      .then(setItems)
      .catch((err) => {
        if ((err as { response?: { status?: number } })?.response?.status === 404) {
          setItems([]);
        } else {
          setError(extractErrorMessage(err, "Couldn't load recommendations."));
        }
      })
      .finally(() => setLoading(false));
  }, [meal]);

  async function handleFeedback(recipeId: number, type: "like" | "dislike") {
    setBusyId(recipeId);
    try {
      await endpoints.submitFeedback({ recipe_id: recipeId, interaction_type: type });
      setFeedback((f) => ({ ...f, [recipeId]: type }));
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't save your feedback."));
    } finally {
      setBusyId(null);
    }
  }

  async function handleLog(recipeId: number) {
    setBusyId(recipeId);
    try {
      await endpoints.logMeal({ recipe_id: recipeId, meal_type: meal });
      setLogged((l) => ({ ...l, [recipeId]: true }));
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't log that meal."));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1 className="mb-6 font-display text-2xl text-ink">Recommendations</h1>

      <MealTabs active={meal} onChange={setMeal} />

      <div className="mt-6">
        {error && (
          <div className="mb-6">
            <ErrorBanner message={error} />
          </div>
        )}

        {loading && <p className="py-8 text-sm text-muted">Finding recipes for {meal.toLowerCase()}…</p>}

        {!loading && items && items.length === 0 && (
          <EmptyState
            title="Nothing fits right now"
            description="Try relaxing an allergy, cooking-time, or diet filter in your profile."
            action={
              <Link to="/profile">
                <Button variant="secondary">Edit profile</Button>
              </Link>
            }
          />
        )}

        {!loading && items && items.length > 0 && (
          <div className="divide-y divide-hairline">
            {items.map((item) => (
              <RecipeRow
                key={item.recipe_id}
                item={item}
                feedback={feedback[item.recipe_id] ?? null}
                logged={Boolean(logged[item.recipe_id])}
                busy={busyId === item.recipe_id}
                onFeedback={(type) => handleFeedback(item.recipe_id, type)}
                onLog={() => handleLog(item.recipe_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
