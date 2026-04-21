const DEFAULT_GATEWAY_URL = "http://localhost:18080";

export type GatewayJsonResponse = {
  ok: boolean;
  status: number;
  data: unknown;
};

export function resolveGatewayUrl(): string {
  const raw =
    process.env.API_GATEWAY_URL ??
    process.env.NEXT_PUBLIC_API_GATEWAY_URL ??
    DEFAULT_GATEWAY_URL;

  return raw.replace(/\/+$/, "");
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function readMessage(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (isRecord(value) && typeof value.message === "string" && value.message.trim()) {
    return value.message;
  }

  return fallback;
}

export async function fetchGatewayJson(
  path: string,
  init: RequestInit = {},
): Promise<GatewayJsonResponse> {
  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const response = await fetch(`${resolveGatewayUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  const bodyText = await response.text();
  let data: unknown = null;

  try {
    data = bodyText ? JSON.parse(bodyText) : null;
  } catch {
    data = bodyText;
  }

  return {
    ok: response.ok,
    status: response.status,
    data,
  };
}
