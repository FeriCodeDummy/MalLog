"use client";

type CookieSetOptions = {
  expiresDays?: number;
  path?: string;
  sameSite?: "Lax" | "Strict" | "None";
  secure?: boolean;
};

function buildCookieString(
  name: string,
  value: string,
  options: CookieSetOptions = {},
): string {
  const path = options.path ?? "/";
  const sameSite = options.sameSite ?? "Lax";
  const secure =
    options.secure ?? (sameSite === "None" || window.location.protocol === "https:");
  const segments = [
    `${encodeURIComponent(name)}=${encodeURIComponent(value)}`,
    `Path=${path}`,
    `SameSite=${sameSite}`,
  ];

  if (typeof options.expiresDays === "number") {
    segments.push(`Max-Age=${Math.max(0, Math.round(options.expiresDays * 24 * 60 * 60))}`);
  }

  if (secure) {
    segments.push("Secure");
  }

  return segments.join("; ");
}

export function Cookies() {
  return {
    get(name: string): string | null {
      const encodedName = `${encodeURIComponent(name)}=`;
      const found = document.cookie
        .split("; ")
        .find((item) => item.startsWith(encodedName));

      if (!found) {
        return null;
      }

      return decodeURIComponent(found.slice(encodedName.length));
    },
    set(name: string, value: string, options: CookieSetOptions = {}) {
      document.cookie = buildCookieString(name, value, options);
    },
    remove(name: string, path = "/") {
      document.cookie = `${encodeURIComponent(name)}=; Path=${path}; Max-Age=0; SameSite=Lax`;
    },
  };
}
