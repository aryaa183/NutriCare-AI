import { type FormEvent, useState } from "react";
import type { AllergyType, Condition, HealthProfileRequest } from "../api/types";
import { Button } from "./Button";
import { ChipGroup, SelectField, TextField } from "./Field";

const ALLERGY_OPTIONS: { value: AllergyType; label: string }[] = [
  { value: "peanut", label: "Peanut" },
  { value: "dairy", label: "Dairy" },
  { value: "egg", label: "Egg" },
  { value: "gluten", label: "Gluten" },
  { value: "soy", label: "Soy" },
  { value: "tree_nut", label: "Tree nut" },
  { value: "fish", label: "Fish" },
  { value: "shellfish", label: "Shellfish" },
  { value: "sesame", label: "Sesame" },
  { value: "mustard", label: "Mustard" },
];

const CONDITION_OPTIONS: { value: Condition; label: string }[] = [
  { value: "diabetes", label: "Diabetes" },
  { value: "hypertension", label: "Hypertension" },
  { value: "heart_disease", label: "Heart disease" },
];

const DEFAULTS: HealthProfileRequest = {
  age: 30,
  gender: "female",
  height_cm: 160,
  weight_kg: 60,
  activity_level: "moderate",
  goal: "general",
  diet_type: "vegetarian",
  regional_preference: "",
  budget_level: undefined,
  max_cooking_time: undefined,
  allergies: [],
  conditions: [],
};

interface HealthProfileFormProps {
  initialValues?: Partial<HealthProfileRequest>;
  onSubmit: (payload: HealthProfileRequest) => Promise<void>;
  submitLabel: string;
  busy?: boolean;
}

export function HealthProfileForm({
  initialValues,
  onSubmit,
  submitLabel,
  busy,
}: HealthProfileFormProps) {
  const [values, setValues] = useState<HealthProfileRequest>({ ...DEFAULTS, ...initialValues });

  function update<K extends keyof HealthProfileRequest>(key: K, value: HealthProfileRequest[K]) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function toggleListValue<T extends string>(key: "allergies" | "conditions", value: T) {
    setValues((v) => {
      const list = v[key] as T[];
      const next = list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
      return { ...v, [key]: next };
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const payload: HealthProfileRequest = {
      ...values,
      regional_preference: values.regional_preference || null,
      budget_level: values.budget_level || null,
      max_cooking_time: values.max_cooking_time || null,
    };
    await onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <section className="space-y-4">
        <h2 className="font-display text-lg text-ink">About you</h2>
        <div className="grid grid-cols-2 gap-4">
          <TextField
            label="Age"
            type="number"
            required
            min={13}
            max={100}
            value={values.age}
            onChange={(e) => update("age", Number(e.target.value))}
          />
          <SelectField
            label="Gender"
            required
            value={values.gender}
            onChange={(e) => update("gender", e.target.value as HealthProfileRequest["gender"])}
            options={[
              { value: "female", label: "Female" },
              { value: "male", label: "Male" },
            ]}
          />
          <TextField
            label="Height (cm)"
            type="number"
            required
            min={100}
            max={250}
            value={values.height_cm}
            onChange={(e) => update("height_cm", Number(e.target.value))}
          />
          <TextField
            label="Weight (kg)"
            type="number"
            required
            min={25}
            max={300}
            value={values.weight_kg}
            onChange={(e) => update("weight_kg", Number(e.target.value))}
          />
          <SelectField
            label="Activity level"
            required
            value={values.activity_level}
            onChange={(e) =>
              update("activity_level", e.target.value as HealthProfileRequest["activity_level"])
            }
            options={[
              { value: "sedentary", label: "Sedentary — little exercise" },
              { value: "light", label: "Light — 1-3 days/week" },
              { value: "moderate", label: "Moderate — 3-5 days/week" },
              { value: "active", label: "Active — 6-7 days/week" },
            ]}
          />
          <SelectField
            label="Goal"
            required
            value={values.goal}
            onChange={(e) => update("goal", e.target.value as HealthProfileRequest["goal"])}
            options={[
              { value: "general", label: "General wellbeing" },
              { value: "weight_loss", label: "Weight loss" },
              { value: "weight_gain", label: "Weight gain" },
            ]}
          />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-lg text-ink">Food preferences</h2>
        <div className="grid grid-cols-2 gap-4">
          <SelectField
            label="Diet type"
            required
            value={values.diet_type}
            onChange={(e) => update("diet_type", e.target.value as HealthProfileRequest["diet_type"])}
            options={[
              { value: "vegetarian", label: "Vegetarian" },
              { value: "non_vegetarian", label: "Non-vegetarian" },
              { value: "eggetarian", label: "Eggetarian" },
              { value: "vegan", label: "Vegan" },
            ]}
          />
          <TextField
            label="Regional preference"
            placeholder="e.g. South, North, East, West"
            value={values.regional_preference ?? ""}
            onChange={(e) => update("regional_preference", e.target.value)}
          />
          <SelectField
            label="Budget"
            value={values.budget_level ?? ""}
            placeholder="No preference"
            onChange={(e) =>
              update("budget_level", (e.target.value || null) as HealthProfileRequest["budget_level"])
            }
            options={[
              { value: "low", label: "Low" },
              { value: "medium", label: "Medium" },
              { value: "flexible", label: "Flexible" },
            ]}
          />
          <TextField
            label="Max cooking time (mins)"
            type="number"
            min={5}
            max={300}
            placeholder="No limit"
            value={values.max_cooking_time ?? ""}
            onChange={(e) =>
              update("max_cooking_time", e.target.value ? Number(e.target.value) : undefined)
            }
          />
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="font-display text-lg text-ink">Health details</h2>
        <ChipGroup
          label="Allergies"
          options={ALLERGY_OPTIONS}
          selected={values.allergies}
          onToggle={(v) => toggleListValue("allergies", v as AllergyType)}
          hint="We'll exclude any recipe containing these — tap to select."
        />
        <ChipGroup
          label="Conditions"
          options={CONDITION_OPTIONS}
          selected={values.conditions}
          onToggle={(v) => toggleListValue("conditions", v as Condition)}
          hint="Recommendations are scored to favor recipes that suit these."
        />
      </section>

      <Button type="submit" busy={busy} className="w-full">
        {submitLabel}
      </Button>
    </form>
  );
}
