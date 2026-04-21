import { NextResponse } from "next/server";

import { getServerAuthenticatedUser } from "@/lib/auth-server";
import { resolveGatewayUrl } from "@/lib/gateway";

export async function POST(request: Request) {
  try {
    const user = await getServerAuthenticatedUser();
    if (!user) {
      return NextResponse.json({ message: "Unauthorized." }, { status: 401 });
    }

    const formData = await request.formData();
    const file = formData.get("file");

    if (!(file instanceof File)) {
      return NextResponse.json(
        { message: "LOG file is required." },
        { status: 400 },
      );
    }

    if (!file.name.toLowerCase().endsWith(".log")) {
      return NextResponse.json(
        { message: "Only .log files are supported." },
        { status: 400 },
      );
    }

    const logText = await file.text();
    if (!logText.trim()) {
      return NextResponse.json(
        { message: "Uploaded LOG file is empty." },
        { status: 400 },
      );
    }

    const gatewayFormData = new FormData();
    gatewayFormData.append("file", file, file.name);

    const gatewayResponse = await fetch(`${resolveGatewayUrl()}/submit`, {
      method: "POST",
      body: gatewayFormData,
      cache: "no-store",
    });

    const bodyText = await gatewayResponse.text();
    let gatewayBody: unknown = null;
    try {
      gatewayBody = bodyText ? JSON.parse(bodyText) : null;
    } catch {
      gatewayBody = bodyText;
    }

    if (!gatewayResponse.ok) {
      return NextResponse.json(
        {
          message: "API gateway call failed.",
          gatewayStatus: gatewayResponse.status,
          gatewayBody,
        },
        { status: gatewayResponse.status },
      );
    }

    const lineCount = logText.split(/\r?\n/).filter((line) => line.trim()).length;

    return NextResponse.json({
      uploadedLog: {
        fileName: file.name,
        sizeBytes: file.size,
        lineCount,
      },
      gatewayResponse: gatewayBody,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { message: `Unexpected server error: ${message}` },
      { status: 500 },
    );
  }
}
