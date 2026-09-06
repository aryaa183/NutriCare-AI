import type { MealType } from "../api/types";

const MEAL_TYPES: MealType[] = ["Breakfast", "Lunch", "Snack", "Dinner"];

interface MealTabsProps {
  active: MealType;
  onChange: (meal: MealType) => void;
}

export function MealTabs({ active, onChange }: MealTabsProps) {
  return (
    <div className="flex gap-6 border-b border-hairline">
      {MEAL_TYPES.map((meal) => {
        const isActive = meal === active;
        return (
          <button
            key={meal}
            type="button"
            onClick={() => onChange(meal)}
            className={`relative -mb-px pb-3 text-sm font-medium transition-colors ${
              isActive ? "text-ink" : "text-muted hover:text-ink"
            }`}
          >
            {meal}
            {isActive && <span className="absolute inset-x-0 -bottom-px h-0.5 bg-brand" />}
          </button>
        );
      })}
    </div>
  );
}
