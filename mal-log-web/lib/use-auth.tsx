"use client";

import { createContext, useContext, useEffect, useState } from "react";

import {
  type AuthenticatedUser,
  isAuthenticatedUser,
  SESSION_COOKIE_EXPIRES_DAYS,
  SESSION_COOKIE_NAME,
} from "@/lib/auth";
import { Cookies } from "@/lib/cookies";
import { isRecord, readMessage } from "@/lib/gateway";

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = {
  name: string;
  surname: string;
  email: string;
  password: string;
};

type AuthContextValue = {
  user: AuthenticatedUser | null;
  sessionID: string | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<AuthenticatedUser>;
  register: (payload: RegisterPayload) => Promise<AuthenticatedUser>;
  logout: () => void;
  refreshSession: (sessionID?: string | null) => Promise<AuthenticatedUser | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

function getStoredSessionID(): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  return Cookies().get(SESSION_COOKIE_NAME);
}

function extractSessionID(value: unknown): string | null {
  if (!isRecord(value) || typeof value.sessionID !== "string" || !value.sessionID.trim()) {
    return null;
  }

  return value.sessionID.trim();
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [initialSessionID] = useState<string | null>(() => getStoredSessionID());
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [sessionID, setSessionID] = useState<string | null>(initialSessionID);
  const [isLoading, setIsLoading] = useState(Boolean(initialSessionID));

  async function hydrateSession(resolvedSessionID: string) {
    try {
      const response = await fetch("/api/auth/session-login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sessionID: resolvedSessionID }),
      });
      const payload = await readJson(response);

      if (!response.ok || !isRecord(payload) || !isAuthenticatedUser(payload.user)) {
        Cookies().remove(SESSION_COOKIE_NAME);
        setSessionID(null);
        setUser(null);
        setIsLoading(false);
        return null;
      }

      setSessionID(resolvedSessionID);
      setUser(payload.user);
      setIsLoading(false);
      return payload.user;
    } catch {
      Cookies().remove(SESSION_COOKIE_NAME);
      setSessionID(null);
      setUser(null);
      setIsLoading(false);
      return null;
    }
  }

  async function refreshSession(nextSessionID?: string | null) {
    const resolvedSessionID = nextSessionID ?? getStoredSessionID();

    if (!resolvedSessionID) {
      Cookies().remove(SESSION_COOKIE_NAME);
      setSessionID(null);
      setUser(null);
      setIsLoading(false);
      return null;
    }

    setSessionID(resolvedSessionID);
    setIsLoading(true);
    return hydrateSession(resolvedSessionID);
  }

  async function establishSession(
    path: "/api/auth/login" | "/api/auth/register",
    payload: LoginPayload | RegisterPayload,
  ) {
    const response = await fetch(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const responseBody = await readJson(response);

    if (!response.ok) {
      throw new Error(readMessage(responseBody, "Authentication request failed."));
    }

    const nextSessionID = extractSessionID(responseBody);
    if (!nextSessionID) {
      throw new Error("Backend did not return a valid session ID.");
    }

    Cookies().set(SESSION_COOKIE_NAME, nextSessionID, {
      expiresDays: SESSION_COOKIE_EXPIRES_DAYS,
    });

    setIsLoading(true);
    const nextUser = await refreshSession(nextSessionID);
    if (!nextUser) {
      throw new Error("Session validation failed.");
    }

    return nextUser;
  }

  async function login(payload: LoginPayload) {
    return establishSession("/api/auth/login", payload);
  }

  async function register(payload: RegisterPayload) {
    return establishSession("/api/auth/register", payload);
  }

  function logout() {
    Cookies().remove(SESSION_COOKIE_NAME);
    setSessionID(null);
    setUser(null);
    setIsLoading(false);
  }

  useEffect(() => {
    if (!initialSessionID) {
      return;
    }

    const timer = window.setTimeout(() => {
      void hydrateSession(initialSessionID);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [initialSessionID]);

  return (
    <AuthContext.Provider
      value={{
        user,
        sessionID,
        isLoading,
        login,
        register,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}
