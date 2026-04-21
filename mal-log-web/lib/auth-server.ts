import { cookies } from "next/headers";

import { type AuthenticatedUser, isAuthenticatedUser, SESSION_COOKIE_NAME } from "@/lib/auth";
import { fetchGatewayJson } from "@/lib/gateway";

function readSessionID(payload: unknown): string | null {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "sessionID" in payload &&
    typeof payload.sessionID === "string" &&
    payload.sessionID.trim()
  ) {
    return payload.sessionID.trim();
  }

  return null;
}

export async function fetchUserBySessionID(
  sessionID: string,
): Promise<AuthenticatedUser | null> {
  try {
    const response = await fetchGatewayJson("/session-login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sessionID }),
    });

    if (!response.ok || !isAuthenticatedUser(response.data)) {
      return null;
    }

    return response.data;
  } catch {
    return null;
  }
}

export async function getServerSessionID(): Promise<string | null> {
  const store = await cookies();
  const sessionID = store.get(SESSION_COOKIE_NAME)?.value;
  return readSessionID({ sessionID });
}

export async function getServerAuthenticatedUser(): Promise<AuthenticatedUser | null> {
  const sessionID = await getServerSessionID();
  if (!sessionID) {
    return null;
  }

  return fetchUserBySessionID(sessionID);
}
