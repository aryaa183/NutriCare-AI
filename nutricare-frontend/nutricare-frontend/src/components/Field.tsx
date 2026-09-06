import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

const labelClasses = "block text-sm font-medium text-ink mb-1.5";
const controlClasses =
  "w-full rounded-sm border border-hairline-strong bg-surface-raised px-3 py-2.5 text-sm text-ink outline-none focus:border-brand transition-colors";

interface FieldWrapProps {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export function FieldWrap({ label, hint, error, children }: FieldWrapProps) {
  return (
    <label className="block">
      <span className={labelClasses}>{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-warn">{error}</span>}
    </label>
  );
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

export function TextField({ label, hint, error, type = "text", className = "", ...rest }: TextFieldProps) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <input type={type} className={`${controlClasses} ${className}`} {...rest} />
    </FieldWrap>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  hint?: string;
  error?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}

export function SelectField({
  label,
  hint,
  error,
  options,
  placeholder,
  className = "",
  ...rest
}: SelectFieldProps) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <select className={`${controlClasses} ${className}`} {...rest}>
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </FieldWrap>
  );
}

interface ChipGroupProps {
  label: string;
  hint?: string;
  options: { value: string; label: string }[];
  selected: string[];
  onToggle: (value: string) => void;
}

export function ChipGroup({ label, hint, options, selected, onToggle }: ChipGroupProps) {
  return (
    <div>
      <span className={labelClasses}>{label}</span>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const active = selected.includes(opt.value);
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onToggle(opt.value)}
              aria-pressed={active}
              className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                active
                  ? "border-brand bg-brand-tint text-brand-dark"
                  : "border-hairline-strong text-muted hover:border-ink hover:text-ink"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      {hint && <span className="mt-1.5 block text-xs text-muted">{hint}</span>}
    </div>
  );
}
