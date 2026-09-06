import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { DashboardResponse } from "../api/types";
import { Button } from "../components/Button";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { MacroBar } from "../components/MacroBar";

export function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    endpoints
      .getDashboard()
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err, "Couldn't load your dashboard.")));
  }, []);

  if (error) return <ErrorBanner message={error} />;
  if (!data) return <div className="text-sm text-muted">Loading…</div>;

  return (
    <div>
      <h1 className="mb-8 font-display text-2xl text-ink">Today</h1>

      <div className="mb-10 rounded-md border border-hairline bg-surface-raised p-8">
        <p className="mb-2 text-sm text-muted">Calories remaining</p>
        <p className="font-tabular font-display text-5xl leading-none text-ink">
          {Math.max(0, Math.round(data.calories_remaining)).toLocaleString()}
        </p>
        <p className="font-tabular mt-2 text-sm text-muted">
          {Math.round(data.calories_consumed)} of {Math.round(data.daily_calorie_target)} kcal consumed
        </p>

        <div className="mt-6">
          <MacroBar
            label="Protein"
            consumed={data.protein_consumed_g}
            target={data.protein_target_g}
          />
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-lg text-ink">Today's meals</h2>
        <Link to="/recommendations" className="text-sm text-brand hover:underline">
          Find something to eat
        </Link>
      </div>

      {data.meals_today.length === 0 ? (
        <EmptyState
          title="Nothing logged yet today"
          description="Get a recommendation and log it once you've eaten to track your progress."
          action={
            <Link to="/recommendations">
              <Button variant="secondary">Browse recommendations</Button>
            </Link>
          }
        />
      ) : (
        <ul className="divide-y divide-hairline border-y border-hairline">
          {data.meals_today.map((meal, i) => (
            <li key={i} className="flex items-center justify-between py-3.5 text-sm">
              <div>
                <span className="mr-3 text-muted">{meal.meal_type}</span>
                <span className="text-ink">{meal.recipe_name}</span>
              </div>
              <span className="font-tabular text-muted">
                {Math.round(meal.calories)} kcal · {Math.round(meal.protein_g)}g
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
