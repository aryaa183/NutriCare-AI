import { History, LayoutDashboard, LogOut, User, UtensilsCrossed } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Logo } from "./Logo";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/recommendations", label: "Recommendations", icon: UtensilsCrossed },
  { to: "/meals", label: "Meal history", icon: History },
  { to: "/profile", label: "Profile", icon: User },
];

export function AppShell({ children }: { children: ReactNode }) {
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen md:flex">
      <aside className="border-hairline bg-surface-raised md:flex md:w-56 md:flex-col md:border-r">
        <div className="flex items-center justify-between px-5 py-5 md:block">
          <Logo className="text-ink" />
          <button
            type="button"
            onClick={logout}
            aria-label="Log out"
            className="text-muted transition-colors hover:text-warn md:hidden"
          >
            <LogOut size={20} strokeWidth={1.75} />
          </button>
        </div>

        <nav className="flex justify-around px-2 pb-2 md:block md:flex-1 md:px-3 md:pb-0">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 rounded-sm px-3 py-2 text-xs transition-colors md:mb-1 md:flex-row md:justify-start md:gap-2.5 md:px-3 md:py-2 md:text-sm ${
                  isActive
                    ? "text-brand-dark md:bg-brand-tint"
                    : "text-muted hover:text-ink md:hover:bg-surface"
                }`
              }
            >
              <Icon size={18} strokeWidth={1.75} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          onClick={logout}
          className="hidden items-center gap-2.5 px-5 py-4 text-sm text-muted transition-colors hover:text-warn md:flex"
        >
          <LogOut size={18} strokeWidth={1.75} />
          Log out
        </button>
      </aside>

      <main className="flex-1 px-5 py-8 md:px-10 md:py-10">
        <div className="mx-auto max-w-3xl">{children}</div>
      </main>
    </div>
  );
}
