import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import { Button } from "../components/Button";
import { ErrorBanner } from "../components/ErrorBanner";
import { TextField } from "../components/Field";
import { Logo } from "../components/Logo";
import { useAuthStore } from "../store/authStore";

export function SignupPage() {
  const navigate = useNavigate();
  const signup = useAuthStore((s) => s.signup);
  const isBusy = useAuthStore((s) => s.isBusy);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await signup({ name, email, password });
      navigate("/onboarding");
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't create your account. Try again."));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <Logo className="mb-8 justify-center" />
        <h1 className="mb-1 font-display text-2xl text-ink">Create your account</h1>
        <p className="mb-6 text-sm text-muted">
          Takes a couple of minutes — we'll ask about your health next.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorBanner message={error} />}
          <TextField
            label="Name"
            required
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <TextField
            label="Email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="At least 8 characters."
          />
          <Button type="submit" busy={isBusy} className="w-full">
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link to="/login" className="text-brand hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
