import { Check, Clock, MapPin, ThumbsDown, ThumbsUp } from "lucide-react";
import type { RecommendationItem } from "../api/types";

interface RecipeRowProps {
  item: RecommendationItem;
  feedback?: "like" | "dislike" | null;
  logged?: boolean;
  onFeedback: (type: "like" | "dislike") => void;
  onLog: () => void;
  busy?: boolean;
}

export function RecipeRow({ item, feedback, logged, onFeedback, onLog, busy }: RecipeRowProps) {
  return (
    <div className="flex gap-4 border-l-2 border-brand/70 py-5 pl-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h3 className="font-display text-base leading-snug text-ink">{item.recipe_name}</h3>
          <span className="font-tabular whitespace-nowrap text-sm text-muted">
            {Math.round(item.calories)} kcal · {Math.round(item.protein_g)}g protein
          </span>
        </div>

        <p className="mt-1 text-sm text-muted">{item.why}</p>

        <div className="mt-2 flex items-center gap-4 text-xs text-muted">
          <span className="flex items-center gap-1">
            <MapPin size={13} /> {item.region}
          </span>
          <span className="flex items-center gap-1">
            <Clock size={13} /> {Math.round(item.cooking_time_mins)} min
          </span>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={() => onFeedback("like")}
            disabled={busy}
            aria-pressed={feedback === "like"}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
              feedback === "like"
                ? "border-good bg-good-tint text-good"
                : "border-hairline-strong text-muted hover:border-ink hover:text-ink"
            }`}
          >
            <ThumbsUp size={13} /> Like
          </button>
          <button
            type="button"
            onClick={() => onFeedback("dislike")}
            disabled={busy}
            aria-pressed={feedback === "dislike"}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
              feedback === "dislike"
                ? "border-warn bg-warn-tint text-warn"
                : "border-hairline-strong text-muted hover:border-ink hover:text-ink"
            }`}
          >
            <ThumbsDown size={13} /> Not for me
          </button>
          <button
            type="button"
            onClick={onLog}
            disabled={busy || logged}
            className={`ml-auto flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed ${
              logged ? "text-good" : "bg-brand text-white hover:bg-brand-dark"
            }`}
          >
            {logged ? (
              <>
                <Check size={13} /> Logged
              </>
            ) : (
              "Log this meal"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
