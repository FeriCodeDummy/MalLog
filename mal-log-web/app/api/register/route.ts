import { NextResponse } from "next/server";

import { fetchGatewayJson, isRecord, readMessage } from "@/lib/gateway";
import type { GatewayJsonResponse } from "@/lib/gateway";

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => null)) as unknown;
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    return NextResponse.json(
      { message: "Request body must be a JSON object." },
      { status: 400 },
    );
  }

  let gatewayResponse: GatewayJsonResponse;
  try {
    gatewayResponse = await fetchGatewayJson("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    return NextResponse.json(
      {
        message:
          error instanceof Error ? error.message : "API gateway is unavailable.",
      },
      { status: 503 },
    );
  }

  if (!gatewayResponse.ok) {
    return NextResponse.json(
      { message: readMessage(gatewayResponse.data, "Registration failed.") },
      { status: gatewayResponse.status },
    );
  }

  if (
    !isRecord(gatewayResponse.data) ||
    typeof gatewayResponse.data.sessionID !== "string" ||
    !gatewayResponse.data.sessionID.trim()
  ) {
    return NextResponse.json(
      { message: "Gateway returned an invalid registration response." },
      { status: 502 },
    );
  }

  return NextResponse.json(
    {
      sessionID: gatewayResponse.data.sessionID.trim(),
      message: readMessage(gatewayResponse.data, "Registration succeeded."),
    },
    { status: 201 },
  );
}
