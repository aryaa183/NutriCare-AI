import { useState } from "react";
import { extractErrorMessage } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { HealthProfileRequest } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { HealthProfileForm } from "../components/HealthProfileForm";
import { useProfileStore } from "../store/profileStore";

export function ProfilePage() {
  const profile = useProfileStore((s) => s.profile);
  const setProfile = useProfileStore((s) => s.set);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(payload: HealthProfileRequest) {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await endpoints.updateProfile(payload);
      setProfile(updated);
      setSaved(true);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't save your changes."));
    } finally {
      setBusy(false);
    }
  }

  if (!profile) return null;

  return (
    <div>
      <h1 className="mb-1 font-display text-2xl text-ink">Your profile</h1>
      <p className="mb-8 text-sm text-muted">
        Changes here immediately affect your daily targets and recommendations.
      </p>

      {saved && (
        <div className="mb-6 rounded-sm border border-good/30 bg-good-tint px-4 py-3 text-sm text-good">
          Saved. Your targets are up to date.
        </div>
      )}
      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} />
        </div>
      )}

      <HealthProfileForm
        initialValues={profile}
        onSubmit={handleSubmit}
        submitLabel="Save changes"
        busy={busy}
      />
    </div>
  );
}
