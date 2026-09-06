export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <circle cx="11" cy="11" r="10" stroke="currentColor" strokeWidth="1.4" />
        <path
          d="M11 5.5c2.8 1 4 3.2 4 5.5s-1.2 4.5-4 5.5c-2.8-1-4-3.2-4-5.5s1.2-4.5 4-5.5Z"
          fill="currentColor"
        />
      </svg>
      <span className="font-display text-lg tracking-tight">NutriCare</span>
    </div>
  );
}
