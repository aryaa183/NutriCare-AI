import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { HealthProfileRequest } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { HealthProfileForm } from "../components/HealthProfileForm";
import { Logo } from "../components/Logo";
import { useProfileStore } from "../store/profileStore";

export function OnboardingPage() {
  const navigate = useNavigate();
  const setProfile = useProfileStore((s) => s.set);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(payload: HealthProfileRequest) {
    setBusy(true);
    setError(null);
    try {
      const profile = await endpoints.createProfile(payload);
      setProfile(profile);
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't save your profile. Check the form and try again."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="mx-auto max-w-lg">
        <Logo className="mb-6" />
        <h1 className="mb-1 font-display text-2xl text-ink">Tell us about yourself</h1>
        <p className="mb-8 text-sm text-muted">
          This sets your daily targets and shapes every recommendation you'll see.
        </p>
        {error && <div className="mb-6">{<ErrorBanner message={error} />}</div>}
        <HealthProfileForm onSubmit={handleSubmit} submitLabel="Save and continue" busy={busy} />
      </div>
    </div>
  );
}
