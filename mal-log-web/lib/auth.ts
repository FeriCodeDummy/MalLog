import { isRecord } from "@/lib/gateway";

export const SESSION_COOKIE_NAME = "mallog_session_id";
export const SESSION_COOKIE_EXPIRES_DAYS = 7;

export type AuthenticatedUser = {
  name: string;
  surname: string;
  email: string;
  sessionID?: string | null;
};

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function isAuthenticatedUser(value: unknown): value is AuthenticatedUser {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.name) &&
    isNonEmptyString(value.surname) &&
    isNonEmptyString(value.email)
  );
}
