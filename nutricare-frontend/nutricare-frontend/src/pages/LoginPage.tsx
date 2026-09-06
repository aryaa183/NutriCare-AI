import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { extractErrorMessage } from "../api/client";
import { Button } from "../components/Button";
import { ErrorBanner } from "../components/ErrorBanner";
import { TextField } from "../components/Field";
import { Logo } from "../components/Logo";
import { useAuthStore } from "../store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const isBusy = useAuthStore((s) => s.isBusy);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login({ email, password });
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't log you in. Check your details and try again."));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <Logo className="mb-8 justify-center" />
        <h1 className="mb-1 font-display text-2xl text-ink">Welcome back</h1>
        <p className="mb-6 text-sm text-muted">Log in to see today's recommendations.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorBanner message={error} />}
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
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" busy={isBusy} className="w-full">
            Log in
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          New here?{" "}
          <Link to="/signup" className="text-brand hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
