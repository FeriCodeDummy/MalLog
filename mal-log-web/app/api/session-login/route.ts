import { NextResponse } from "next/server";

import { fetchUserBySessionID, getServerSessionID } from "@/lib/auth-server";

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => null)) as unknown;
  const sessionID =
    typeof payload === "object" &&
    payload !== null &&
    "sessionID" in payload &&
    typeof payload.sessionID === "string" &&
    payload.sessionID.trim()
      ? payload.sessionID.trim()
      : await getServerSessionID();

  if (!sessionID) {
    return NextResponse.json({ message: "Not authenticated." }, { status: 401 });
  }

  const user = await fetchUserBySessionID(sessionID);
  if (!user) {
    return NextResponse.json({ message: "Session is invalid or expired." }, { status: 401 });
  }

  return NextResponse.json({ user }, { status: 200 });
}
