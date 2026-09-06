import { type ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  busy?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary: "bg-brand text-white hover:bg-brand-dark disabled:bg-hairline-strong",
  secondary:
    "bg-transparent text-ink border border-hairline-strong hover:border-ink disabled:opacity-50",
  ghost: "bg-transparent text-muted hover:text-ink disabled:opacity-50",
  danger: "bg-transparent text-warn border border-warn/40 hover:bg-warn-tint disabled:opacity-50",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", busy, className = "", children, disabled, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || busy}
        className={`inline-flex items-center justify-center gap-2 rounded-sm px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
        {...rest}
      >
        {busy ? "Working…" : children}
      </button>
    );
  },
);
Button.displayName = "Button";
