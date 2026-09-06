import { type ReactNode, useEffect } from "react";
import { Navigate } from "react-router-dom";
import { useProfileStore } from "../store/profileStore";

export function RequireProfile({ children }: { children: ReactNode }) {
  const status = useProfileStore((s) => s.status);
  const fetch = useProfileStore((s) => s.fetch);

  useEffect(() => {
    if (status === "idle") fetch();
  }, [status, fetch]);

  if (status === "idle" || status === "loading") {
    return <div className="px-10 py-16 text-sm text-muted">Loading your profile…</div>;
  }
  if (status === "missing") {
    return <Navigate to="/onboarding" replace />;
  }
  return <>{children}</>;
}
