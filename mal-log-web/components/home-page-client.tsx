"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useState, useTransition } from "react";

import { isRecord, readMessage } from "@/lib/gateway";
import { useAuth } from "@/lib/use-auth";

type UploadedLogSummary = {
  fileName: string;
  sizeBytes: number;
  lineCount: number;
};

type GatewayAnomalyResponse = {
  file_name?: string;
  uid?: string;
  response?: unknown;
};

type DetectionMetrics = Record<string, number>;

type DetectionResultPayload = {
  label?: string;
  score?: number;
  reasons?: string[];
  metrics?: DetectionMetrics;
};

type DetectionResponsePayload = {
  uid?: string;
  started_at?: string;
  ended_at?: string;
  result?: DetectionResultPayload;
};

type GatewayResponse = {
  processed_files?: number;
  successful_files?: number;
  failed_files?: number;
  anomaly_detection_responses?: GatewayAnomalyResponse[];
  [key: string]: unknown;
};

type AnalyzeResult = {
  uploadedLog: UploadedLogSummary;
  gatewayResponse: GatewayResponse;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

type LabelKind = "ANOMALY" | "NORMAL" | "WARNING" | "UNKNOWN";

function normalizeLabelKind(label: string | undefined): LabelKind {
  const normalized = label?.trim().toUpperCase();
  if (!normalized) return "UNKNOWN";
  if (normalized === "ANOMALY") return "ANOMALY";
  if (normalized === "NORMAL") return "NORMAL";
  if (normalized === "WARNING" || normalized === "WARN") return "WARNING";
  return "UNKNOWN";
}

function labelStyles(label: LabelKind) {
  if (label === "ANOMALY") {
    return {
      badgeClass:
        "border border-[rgba(255,111,97,0.45)] bg-[rgba(255,111,97,0.14)] text-[var(--danger)]",
      scoreColor: "var(--danger)",
      cardGlow: "shadow-[0_0_0_1px_rgba(255,111,97,0.25)_inset]",
    };
  }
  if (label === "NORMAL") {
    return {
      badgeClass:
        "border border-[rgba(116,240,183,0.45)] bg-[rgba(116,240,183,0.14)] text-[var(--success)]",
      scoreColor: "var(--success)",
      cardGlow: "shadow-[0_0_0_1px_rgba(116,240,183,0.22)_inset]",
    };
  }
  if (label === "WARNING") {
    return {
      badgeClass:
        "border border-[rgba(255,201,102,0.45)] bg-[rgba(255,201,102,0.14)] text-[#ffc966]",
      scoreColor: "#ffc966",
      cardGlow: "shadow-[0_0_0_1px_rgba(255,201,102,0.20)_inset]",
    };
  }
  return {
    badgeClass:
      "border border-[var(--panel-border)] bg-[rgba(148,163,184,0.12)] text-[var(--text-muted)]",
    scoreColor: "var(--accent)",
    cardGlow: "",
  };
}

function formatMetricValue(key: string, value: number): string {
  if (key === "total_entries") return value.toLocaleString();
  if (key.endsWith("_ratio")) return `${(value * 100).toFixed(1)}%`;
  if (Math.abs(value) >= 1000) return value.toLocaleString();
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(3);
}

function metricLabel(key: string): string {
  const known: Record<string, string> = {
    total_entries: "Total Entries",
    error_ratio: "Error Ratio",
    warn_ratio: "Warn Ratio",
    status_4xx_5xx_ratio: "4xx/5xx Ratio",
    status_5xx_ratio: "5xx Ratio",
    attack_path_ratio: "Attack Path Ratio",
    normal_path_ratio: "Normal Path Ratio",
    warning_path_ratio: "Warning Path Ratio",
    attacker_ip_ratio: "Attacker IP Ratio",
    dominant_ip_ratio: "Dominant IP Ratio",
    suspicious_messages: "Suspicious Messages",
  };

  if (known[key]) return known[key];

  return key
    .split("_")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

function asDetectionPayload(value: unknown): DetectionResponsePayload | null {
  if (!isRecord(value)) return null;
  return value as DetectionResponsePayload;
}

function formatTimestamp(value: string | undefined): string {
  if (!value) return "n/a";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatDuration(startedAt: string | undefined, endedAt: string | undefined): string {
  if (!startedAt || !endedAt) return "n/a";
  const start = new Date(startedAt).getTime();
  const end = new Date(endedAt).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return "n/a";
  const ms = Math.max(0, end - start);
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function readLabel(payload: DetectionResponsePayload | null): string | undefined {
  if (!payload) return undefined;
  const candidate = payload.result?.label;
  if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  const fallbackLabel = isRecord(payload)
    ? (payload as Record<string, unknown>)["label"]
    : undefined;
  if (typeof fallbackLabel === "string" && fallbackLabel.trim()) {
    return fallbackLabel.trim();
  }
  return undefined;
}

export default function HomePageClient() {
  const router = useRouter();
  const { isLoading: isAuthLoading, logout, user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [isRedirecting, startRedirect] = useTransition();

  const hasResult = !!result;
  const anomalyResponses = result?.gatewayResponse?.anomaly_detection_responses ?? [];

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.replace("/login");
    }
  }, [isAuthLoading, router, user]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setError(null);
    setResult(null);
    setFile(selected);

    if (!selected) {
      setPreviewRows([]);
      return;
    }

    try {
      const text = await selected.text();
      const lines = text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .slice(0, 6);
      setPreviewRows(lines);
    } catch {
      setPreviewRows([]);
      setError("Could not read file preview.");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!file) {
      setError("Select a LOG file first.");
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const payload = (await response.json().catch(() => null)) as unknown;
      if (!response.ok) {
        throw new Error(readMessage(payload, "Failed to call API gateway."));
      }

      setResult(payload as AnalyzeResult);
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Unexpected request error.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLogout() {
    setAuthError(null);
    setIsSigningOut(true);

    try {
      logout();
      startRedirect(() => {
        router.replace("/login");
      });
    } catch (logoutError) {
      setAuthError(
        logoutError instanceof Error
          ? logoutError.message
          : "Unexpected logout failure.",
      );
    } finally {
      setIsSigningOut(false);
    }
  }

  const isLogoutBusy = isSigningOut || isRedirecting;

  if (isAuthLoading || !user) {
    return (
      <main className="relative min-h-dvh overflow-hidden px-5 py-10 md:px-10">
        <div
          aria-hidden
          className="pointer-events-none absolute left-[-18rem] top-[-12rem] h-[30rem] w-[30rem] rounded-full bg-[var(--accent-soft)] blur-3xl"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute bottom-[-14rem] right-[-20rem] h-[34rem] w-[34rem] rounded-full bg-[rgba(116,240,183,0.08)] blur-3xl"
        />
        <section className="mx-auto flex min-h-[60dvh] w-full max-w-4xl items-center justify-center">
          <div className="panel-surface fade-up p-8 text-center">
            <p className="mono text-xs uppercase tracking-[0.3em] text-[var(--accent)]">
              Session Check
            </p>
            <h1 className="mt-4 text-3xl font-semibold">Validating access</h1>
            <p className="mt-3 text-sm text-[var(--text-muted)]">
              Reading the stored session and requesting the current account.
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="relative overflow-hidden px-5 py-10 md:px-10">
      <div
        aria-hidden
        className="pointer-events-none absolute left-[-18rem] top-[-12rem] h-[30rem] w-[30rem] rounded-full bg-[var(--accent-soft)] blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-14rem] right-[-20rem] h-[34rem] w-[34rem] rounded-full bg-[rgba(116,240,183,0.08)] blur-3xl"
      />

      <section className="fade-up mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="panel-surface p-6 shadow-[0_8px_40px_rgba(0,0,0,0.35)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <p className="mono text-xs uppercase tracking-[0.3em] text-[var(--accent)]">
                MalLog Studio
              </p>
              <h1 className="mt-2 text-3xl font-semibold leading-tight md:text-4xl">
                Authenticated gateway workspace for log analysis.
              </h1>
              <p className="mt-3 text-sm text-[var(--text-muted)] md:text-base">
                Upload LOG files, trigger the end-to-end pipeline, and inspect anomaly
                results from the protected homepage after session validation.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
              <div className="rounded-2xl border border-[var(--panel-border)] bg-[rgba(8,12,18,0.66)] px-4 py-3">
                <p className="mono text-[10px] uppercase tracking-[0.16em] text-[var(--text-muted)]">
                  Signed In As
                </p>
                <p className="mt-1 font-semibold">
                  {user.name} {user.surname}
                </p>
                <p className="text-sm text-[var(--text-muted)]">{user.email}</p>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                disabled={isLogoutBusy}
                className="secondary-button min-h-14 min-w-32 justify-center"
              >
                {isLogoutBusy ? "Signing out..." : "Logout"}
              </button>
            </div>
          </div>

          {authError ? <p className="status-banner status-banner--error mt-4">{authError}</p> : null}
        </header>

        <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
          <form
            onSubmit={handleSubmit}
            className="panel-surface fade-up p-6 backdrop-blur-xl"
          >
            <h2 className="text-xl font-medium">1. Select LOG</h2>
            <label
              htmlFor="log-upload"
              className={`mt-4 flex min-h-44 cursor-pointer flex-col justify-between rounded-2xl border border-dashed border-[var(--panel-border)] bg-[rgba(8,12,18,0.65)] p-5 transition ${
                file ? "pulse-border border-[var(--accent)]" : "hover:border-[var(--accent)]"
              }`}
            >
              <div>
                <p className="text-sm uppercase tracking-[0.16em] text-[var(--text-muted)]">
                  LOG Upload
                </p>
                <p className="mt-3 text-lg">
                  {file ? file.name : "Click to choose a .log file"}
                </p>
              </div>
              <p className="mono mt-6 text-xs text-[var(--text-muted)]">
                {file ? `${formatBytes(file.size)} selected` : "Only .log files are accepted"}
              </p>
            </label>
            <input
              id="log-upload"
              type="file"
              accept=".log,text/plain"
              onChange={handleFileChange}
              className="hidden"
            />

            <div className="mt-4 rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-4">
              <p className="mono text-xs uppercase tracking-[0.18em] text-[var(--text-muted)]">
                Preview
              </p>
              {previewRows.length > 0 ? (
                <ul className="mono mt-2 space-y-2 text-xs text-[var(--text-muted)]">
                  {previewRows.map((row, index) => (
                    <li key={`${row}-${index}`} className="truncate">
                      {row}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  First rows will appear here after selecting a file.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="mt-5 inline-flex h-12 w-full items-center justify-center rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[#061018] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? "Running gateway analysis..." : "2. Run Analysis"}
            </button>

            {error ? <p className="status-banner status-banner--error mt-3">{error}</p> : null}
          </form>

          <section className="panel-surface fade-up p-6 backdrop-blur-xl">
            <h2 className="text-xl font-medium">3. Gateway Response</h2>

            {!hasResult ? (
              <p className="mt-4 text-sm text-[var(--text-muted)]">
                Upload LOG and start analysis to view gateway output here.
              </p>
            ) : (
              <div className="mt-4 space-y-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-3">
                    <p className="mono text-[10px] uppercase tracking-[0.16em] text-[var(--text-muted)]">
                      Processed
                    </p>
                    <p className="mt-1 text-2xl font-semibold">
                      {result.gatewayResponse.processed_files ?? 0}
                    </p>
                  </div>
                  <div className="rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-3">
                    <p className="mono text-[10px] uppercase tracking-[0.16em] text-[var(--text-muted)]">
                      Success
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-[var(--success)]">
                      {result.gatewayResponse.successful_files ?? 0}
                    </p>
                  </div>
                  <div className="rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-3">
                    <p className="mono text-[10px] uppercase tracking-[0.16em] text-[var(--text-muted)]">
                      Failed
                    </p>
                    <p className="mt-1 text-2xl font-semibold text-[var(--danger)]">
                      {result.gatewayResponse.failed_files ?? 0}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-4">
                  <p className="mono text-xs uppercase tracking-[0.16em] text-[var(--text-muted)]">
                    Uploaded LOG
                  </p>
                  <p className="mt-2 text-sm">
                    {result.uploadedLog.fileName} | {formatBytes(result.uploadedLog.sizeBytes)} |{" "}
                    {result.uploadedLog.lineCount} lines
                  </p>
                </div>

                <div className="rounded-xl border border-[var(--panel-border)] bg-[rgba(10,15,22,0.65)] p-4">
                  <p className="mono text-xs uppercase tracking-[0.16em] text-[var(--text-muted)]">
                    Anomaly Responses ({anomalyResponses.length})
                  </p>
                  {anomalyResponses.length === 0 ? (
                    <p className="mt-2 text-sm text-[var(--text-muted)]">
                      No anomaly payloads returned.
                    </p>
                  ) : (
                    <div className="mt-3 space-y-4">
                      {anomalyResponses.map((item, index) => {
                        const payload = asDetectionPayload(item.response);
                        const detection = payload?.result;
                        const rawLabel = readLabel(payload);
                        const labelKind = normalizeLabelKind(rawLabel);
                        const labelText = rawLabel?.toUpperCase() ?? "UNKNOWN";
                        const styles = labelStyles(labelKind);
                        const scoreValue = isNumber(detection?.score) ? detection.score : null;
                        const scorePercent = scoreValue !== null
                          ? Math.max(0, Math.min(1, scoreValue)) * 100
                          : null;
                        const reasons = Array.isArray(detection?.reasons)
                          ? detection.reasons
                          : [];
                        const metrics = isRecord(detection?.metrics)
                          ? Object.entries(detection.metrics)
                              .filter(([, value]) => isNumber(value))
                              .map(([key, value]) => [key, value as number] as const)
                          : [];

                        return (
                          <article
                            key={`${item.uid ?? "uid"}-${index}`}
                            className={`rounded-xl border border-[var(--panel-border)] bg-[rgba(8,12,18,0.78)] p-4 ${styles.cardGlow}`}
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-base font-semibold">{item.file_name ?? "n/a"}</p>
                              <span
                                className={`mono rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.14em] ${styles.badgeClass}`}
                              >
                                {labelText}
                              </span>
                              <span className="mono rounded-full border border-[var(--panel-border)] px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                UID {payload?.uid ?? item.uid ?? "n/a"}
                              </span>
                            </div>

                            <div className="mt-3 grid gap-3 sm:grid-cols-2">
                              <div className="rounded-lg border border-[var(--panel-border)] bg-[rgba(12,18,27,0.78)] p-3">
                                <p className="mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                  Score
                                </p>
                                <p className="mt-1 text-2xl font-semibold">
                                  {scoreValue !== null ? scoreValue.toFixed(3) : "n/a"}
                                </p>
                                <div className="mt-2 h-2 overflow-hidden rounded-full bg-[rgba(148,163,184,0.2)]">
                                  <div
                                    className="h-full rounded-full transition-all"
                                    style={{
                                      width: `${scorePercent ?? 0}%`,
                                      backgroundColor: styles.scoreColor,
                                    }}
                                  />
                                </div>
                              </div>

                              <div className="rounded-lg border border-[var(--panel-border)] bg-[rgba(12,18,27,0.78)] p-3">
                                <p className="mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                  Time
                                </p>
                                <p className="mt-1 text-sm text-[var(--text-muted)]">
                                  Start: {formatTimestamp(payload?.started_at)}
                                </p>
                                <p className="text-sm text-[var(--text-muted)]">
                                  End: {formatTimestamp(payload?.ended_at)}
                                </p>
                                <p className="mt-1 text-sm">
                                  Duration: {formatDuration(payload?.started_at, payload?.ended_at)}
                                </p>
                              </div>
                            </div>

                            {metrics.length > 0 ? (
                              <div className="mt-3">
                                <p className="mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                  Key Metrics
                                </p>
                                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                                  {metrics.map(([key, value]) => (
                                    <div
                                      key={key}
                                      className="rounded-md border border-[var(--panel-border)] bg-[rgba(12,18,27,0.78)] px-3 py-2"
                                    >
                                      <p className="mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                        {metricLabel(key)}
                                      </p>
                                      <p className="mt-1 text-sm font-medium">
                                        {formatMetricValue(key, value)}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : null}

                            {reasons.length > 0 ? (
                              <div className="mt-3">
                                <p className="mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
                                  Reasons
                                </p>
                                <ul className="mt-2 space-y-2">
                                  {reasons.map((reason, reasonIndex) => (
                                    <li
                                      key={`${reason}-${reasonIndex}`}
                                      className="rounded-md border border-[var(--panel-border)] bg-[rgba(12,18,27,0.78)] px-3 py-2 text-sm text-[var(--text-muted)]"
                                    >
                                      {reason}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            ) : null}
                          </article>
                        );
                      })}
                    </div>
                  )}
                </div>

                <details className="rounded-xl border border-[var(--panel-border)] bg-[rgba(8,12,18,0.7)] p-4">
                  <summary className="mono cursor-pointer text-xs uppercase tracking-[0.16em] text-[var(--text-muted)]">
                    Raw Gateway JSON
                  </summary>
                  <pre className="mono mt-3 overflow-x-auto text-xs text-[var(--text-muted)]">
                    {JSON.stringify(result.gatewayResponse, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}
