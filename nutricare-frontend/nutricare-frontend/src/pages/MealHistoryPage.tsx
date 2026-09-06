import { useEffect, useState } from "react";
import { extractErrorMessage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { MealLogHistoryItem } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";

export function MealHistoryPage() {
  const [logs, setLogs] = useState<MealLogHistoryItem[] | null>(null);
  const [names, setNames] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    endpoints
      .getMealHistory()
      .then(async (history) => {
        setLogs(history);
        const uniqueIds = [...new Set(history.map((h) => h.recipe_id))];
        const entries = await Promise.all(
          uniqueIds.map(async (id) => {
            try {
              const recipe = await endpoints.getRecipe(id);
              return [id, recipe.recipe_name] as const;
            } catch {
              return [id, "Unknown recipe"] as const;
            }
          }),
        );
        setNames(Object.fromEntries(entries));
      })
      .catch((err) => setError(extractErrorMessage(err, "Couldn't load your meal history.")));
  }, []);

  if (error) return <ErrorBanner message={error} />;
  if (!logs) return <div className="text-sm text-muted">Loading…</div>;

  return (
    <div>
      <h1 className="mb-8 font-display text-2xl text-ink">Meal history</h1>

      {logs.length === 0 ? (
        <EmptyState
          title="No meals logged yet"
          description="Once you log a recommendation, it'll show up here."
        />
      ) : (
        <ul className="divide-y divide-hairline border-y border-hairline">
          {logs.map((log, i) => (
            <li key={i} className="flex items-center justify-between py-3.5 text-sm">
              <div>
                <span className="mr-3 text-muted">{log.meal_type}</span>
                <span className="text-ink">{names[log.recipe_id] ?? "…"}</span>
              </div>
              <span className="font-tabular text-xs text-muted">
                {new Date(log.consumed_at).toLocaleString(undefined, {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
