import crypto from "crypto";
import express from "express";
import swaggerUi from "swagger-ui-express";

import { createDbPool } from "./db";
import * as defaultQueries from "./dbq";
import { openApiSpec } from "./openapi";
import { QueryModule } from "./types";

interface AppOptions {
  db?: unknown | null;
  queries?: QueryModule;
}

function hashPassword(password: string): string {
  return crypto.createHash("sha256").update(password, "utf8").digest("hex");
}

function isString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function createApp(options: AppOptions = {}) {
  const app = express();
  const db = options.db === undefined ? createDbPool() : options.db;
  const queries: QueryModule =
    options.queries ?? (defaultQueries as unknown as QueryModule);

  app.use(express.json());

  app.use((req, res, next) => {
    if (req.method === "OPTIONS") {
      res.setHeader("X-Content-Type-Options", "*");
      return res.status(204).send();
    }
    return next();
  });

  app.get("/openapi.json", (_req, res) => {
    res.status(200).json(openApiSpec);
  });

  app.use("/swagger-ui", swaggerUi.serve, swaggerUi.setup(openApiSpec));

  app.post("/login", async (req, res) => {
    if (!db) {
      return res.status(503).json({ message: "Database unavailable" });
    }

    const { email, password } = req.body ?? {};
    if (!isString(email) || !isString(password)) {
      return res.status(422).json({ message: "Validation error" });
    }

    const account = await queries.accountLogin(db, email, hashPassword(password));
    if (!account) {
      return res.status(400).json({ message: "wrong credentials" });
    }

    return res.status(200).json(account);
  });

  app.post("/session-login", async (req, res) => {
    if (!db) {
      return res.status(503).json({ message: "Database unavailable" });
    }

    const { sessionID } = req.body ?? {};
    if (!isString(sessionID)) {
      return res.status(400).json({ message: "Missing required parameter 'sessionID'" });
    }

    const session = await queries.fetchSessionData(db, sessionID);
    if (!session) {
      return res.status(401).json({ message: "invalid session" });
    }

    return res.status(200).json(session);
  });

  app.post("/register", async (req, res) => {
    if (!db) {
      return res.status(503).json({ message: "Database unavailable" });
    }

    const { name, surname, email, password } = req.body ?? {};
    if (!isString(name) || !isString(surname) || !isString(email) || !isString(password)) {
      return res.status(422).json({ message: "Validation error" });
    }

    const userId = await queries.insertUser(db, name, surname, email, hashPassword(password));
    if (!userId) {
      return res.status(400).json({ message: "bad data" });
    }

    const sessionId = await queries.insertSession(db, userId, email);
    return res.status(201).json({ message: "successful registration", sessionID: sessionId });
  });

  app.get("/.well-known/jwks.json", (_req, res) => {
    res.status(503).json({ message: "Not implemented" });
  });

  app.post("/refresh-jwt", (_req, res) => {
    res.status(503).json({ message: "Not implemented" });
  });

  app.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok" });
  });

  return app;
}
