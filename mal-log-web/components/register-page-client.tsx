"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState, useTransition } from "react";

import AuthShell from "@/components/auth-shell";
import { useAuth } from "@/lib/use-auth";

export default function RegisterPageClient() {
  const router = useRouter();
  const { isLoading, register, user } = useAuth();
  const [name, setName] = useState("");
  const [surname, setSurname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRedirecting, startRedirect] = useTransition();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/");
    }
  }, [isLoading, router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setStatus(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({ name, surname, email, password });
      setStatus("Account created. Redirecting to your workspace...");
      startRedirect(() => {
        router.replace("/");
      });
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Unexpected registration error.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const isBusy = isSubmitting || isRedirecting;

  return (
    <AuthShell
      eyebrow="MalLog Onboarding"
      title="Create a secured workspace entry."
      description="Register a new operator profile, establish a session, and move directly into the protected homepage."
      alternateHref="/login"
      alternateLabel="Sign in"
      alternateText="Already have access?"
      highlights={[
        {
          label: "Identity",
          value: "Profile + Session",
          detail: "Registration creates the user record and issues a session in the auth database.",
        },
        {
          label: "Access Model",
          value: "Protected Home",
          detail: "The homepage becomes available only after a successful validated session.",
        },
        {
          label: "Gateway Role",
          value: "Auth Proxy",
          detail: "The API gateway now exposes auth routes so the web app never talks to auth directly.",
        },
      ]}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="mono text-xs uppercase tracking-[0.24em] text-[var(--accent)]">
            Register
          </p>
          <h2 className="mt-3 text-3xl font-semibold">Create Account</h2>
        </div>
        <Link href="/login" className="secondary-button shrink-0">
          Sign In
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label htmlFor="name" className="field-label">
              Name
            </label>
            <input
              id="name"
              type="text"
              autoComplete="given-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="field-input"
              placeholder="Ana"
              required
            />
          </div>

          <div>
            <label htmlFor="surname" className="field-label">
              Surname
            </label>
            <input
              id="surname"
              type="text"
              autoComplete="family-name"
              value={surname}
              onChange={(event) => setSurname(event.target.value)}
              className="field-input"
              placeholder="Smith"
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="email" className="field-label">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="field-input"
            placeholder="ana@example.com"
            required
          />
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label htmlFor="password" className="field-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="field-input"
              placeholder="Choose a password"
              required
            />
          </div>

          <div>
            <label htmlFor="confirm-password" className="field-label">
              Confirm Password
            </label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              minLength={6}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="field-input"
              placeholder="Repeat password"
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isBusy}
          className="mt-2 inline-flex h-12 w-full items-center justify-center rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[#061018] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isBusy ? "Provisioning..." : "Create Workspace Access"}
        </button>

        {status ? <p className="status-banner status-banner--success">{status}</p> : null}
        {error ? <p className="status-banner status-banner--error">{error}</p> : null}
      </form>
    </AuthShell>
  );
}
