import Link from "next/link";
import type { ReactNode } from "react";

type Highlight = {
  label: string;
  value: string;
  detail: string;
};

type AuthShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  alternateHref: string;
  alternateLabel: string;
  alternateText: string;
  children: ReactNode;
  highlights: Highlight[];
};

export default function AuthShell({
  eyebrow,
  title,
  description,
  alternateHref,
  alternateLabel,
  alternateText,
  children,
  highlights,
}: AuthShellProps) {
  return (
    <main className="relative min-h-dvh overflow-hidden px-5 py-10 md:px-10">
      <div
        aria-hidden
        className="pointer-events-none absolute left-[-18rem] top-[-11rem] h-[30rem] w-[30rem] rounded-full bg-[var(--accent-soft)] blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-16rem] right-[-18rem] h-[33rem] w-[33rem] rounded-full bg-[rgba(116,240,183,0.12)] blur-3xl"
      />

      <section className="mx-auto grid w-full max-w-6xl gap-6 lg:grid-cols-[1.08fr_0.92fr]">
        <div className="panel-surface fade-up relative overflow-hidden p-7 md:p-8">
          <div
            aria-hidden
            className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[rgba(51,208,255,0.45)] to-transparent"
          />

          <p className="mono text-xs uppercase tracking-[0.3em] text-[var(--accent)]">
            {eyebrow}
          </p>
          <h1 className="mt-4 max-w-xl text-4xl font-semibold leading-tight md:text-5xl">
            {title}
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--text-muted)] md:text-base">
            {description}
          </p>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            {highlights.map((item) => (
              <article
                key={item.label}
                className="rounded-2xl border border-[var(--panel-border)] bg-[rgba(8,12,18,0.6)] p-4"
              >
                <p className="mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">
                  {item.label}
                </p>
                <p className="mt-3 text-2xl font-semibold text-[var(--text)]">{item.value}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{item.detail}</p>
              </article>
            ))}
          </div>

          <div className="mt-8 rounded-3xl border border-[var(--panel-border)] bg-[rgba(7,10,15,0.72)] p-5">
            <p className="mono text-[10px] uppercase tracking-[0.22em] text-[var(--success)]">
              Mission
            </p>
            <p className="mt-3 text-lg font-medium">
              Security analysis starts with a controlled entry point.
            </p>
            <p className="mt-3 max-w-lg text-sm leading-7 text-[var(--text-muted)]">
              Every sign-in flows through the API gateway before reaching the auth service,
              matching the same service boundaries used by the rest of the platform.
            </p>
          </div>
        </div>

        <div className="panel-surface fade-up p-7 md:p-8">
          {children}
          <p className="mt-6 text-sm text-[var(--text-muted)]">
            {alternateText}{" "}
            <Link href={alternateHref} className="text-link font-medium">
              {alternateLabel}
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
