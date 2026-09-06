import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MealHistoryPage } from "./pages/MealHistoryPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { SignupPage } from "./pages/SignupPage";
import { RequireAuth } from "./routes/RequireAuth";
import { RequireProfile } from "./routes/RequireProfile";

function Protected({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <RequireProfile>
        <AppShell>{children}</AppShell>
      </RequireProfile>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/onboarding"
        element={
          <RequireAuth>
            <OnboardingPage />
          </RequireAuth>
        }
      />

      <Route
        path="/dashboard"
        element={
          <Protected>
            <DashboardPage />
          </Protected>
        }
      />
      <Route
        path="/recommendations"
        element={
          <Protected>
            <RecommendationsPage />
          </Protected>
        }
      />
      <Route
        path="/meals"
        element={
          <Protected>
            <MealHistoryPage />
          </Protected>
        }
      />
      <Route
        path="/profile"
        element={
          <Protected>
            <ProfilePage />
          </Protected>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
