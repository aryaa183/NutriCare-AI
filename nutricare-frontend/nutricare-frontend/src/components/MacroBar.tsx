interface MacroBarProps {
  label: string;
  consumed: number;
  target: number;
  unit?: string;
}

export function MacroBar({ label, consumed, target, unit = "g" }: MacroBarProps) {
  const pct = target > 0 ? Math.min(100, Math.round((consumed / target) * 100)) : 0;
  const over = consumed > target;

  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="font-tabular text-muted">
          {Math.round(consumed)}
          {unit} <span className="text-hairline-strong">/</span> {Math.round(target)}
          {unit}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface">
        <div
          className={`h-full rounded-full transition-all ${over ? "bg-warn" : "bg-good"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
