"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState, useTransition } from "react";

import AuthShell from "@/components/auth-shell";
import { useAuth } from "@/lib/use-auth";

export default function LoginPageClient() {
  const router = useRouter();
  const { isLoading, login, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    setIsSubmitting(true);

    try {
      await login({ email, password });
      setStatus("Session established. Redirecting to your workspace...");
      startRedirect(() => {
        router.replace("/");
      });
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Unexpected login error.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const isBusy = isSubmitting || isRedirecting;

  return (
    <AuthShell
      eyebrow="MalLog Access"
      title="Sign in to the analysis workspace."
      description="Return to the authenticated dashboard for log uploads, anomaly review, and gateway-tracked activity."
      alternateHref="/register"
      alternateLabel="Create an account"
      alternateText="Need a new workspace?"
      highlights={[
        {
          label: "Gateway Path",
          value: "Web -> API",
          detail: "Credentials travel through the API gateway boundary before auth validation.",
        },
        {
          label: "Session TTL",
          value: "7 Days",
          detail: "The current auth schema provisions a server-side session with a one-week lifetime.",
        },
        {
          label: "Landing",
          value: "/",
          detail: "Successful authentication returns you directly to the protected homepage.",
        },
      ]}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="mono text-xs uppercase tracking-[0.24em] text-[var(--accent)]">
            Login
          </p>
          <h2 className="mt-3 text-3xl font-semibold">Authenticate</h2>
        </div>
        <Link href="/register" className="secondary-button shrink-0">
          Register
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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

        <div>
          <label htmlFor="password" className="field-label">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="field-input"
            placeholder="Enter your password"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isBusy}
          className="mt-2 inline-flex h-12 w-full items-center justify-center rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[#061018] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isBusy ? "Authorizing..." : "Sign In"}
        </button>

        {status ? <p className="status-banner status-banner--success">{status}</p> : null}
        {error ? <p className="status-banner status-banner--error">{error}</p> : null}
      </form>
    </AuthShell>
  );
}
