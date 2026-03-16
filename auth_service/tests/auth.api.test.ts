import crypto from "crypto";
import request from "supertest";

import { createApp } from "../src/app";
import { QueryModule } from "../src/types";

function buildQueries(overrides: Partial<QueryModule> = {}): QueryModule {
  return {
    accountLogin: async () => null,
    fetchSessionData: async () => null,
    insertUser: async () => null,
    insertSession: async () => null,
    ...overrides
  };
}

describe("express ts auth service", () => {
  test("openapi spec is available", async () => {
    const app = createApp({ db: {}, queries: buildQueries() });
    const res = await request(app).get("/openapi.json");
    expect(res.statusCode).toBe(200);
    expect(res.body.openapi).toMatch(/^3\./);
    expect(res.body.paths["/login"]).toBeDefined();
  });

  test("swagger ui is available", async () => {
    const app = createApp({ db: {}, queries: buildQueries() });
    const res = await request(app).get("/swagger-ui");
    expect(res.statusCode).toBe(301);
  });

  test("login success hashes password", async () => {
    const spy = jest.fn(async () => ({
      name: "Jane",
      surname: "Doe",
      email: "jane@example.com",
      sessionID: "sid-123"
    }));

    const queries = buildQueries({ accountLogin: spy });
    const app = createApp({ db: {}, queries });

    const res = await request(app)
      .post("/login")
      .send({ email: "jane@example.com", password: "top-secret" });

    expect(res.statusCode).toBe(200);
    expect(res.body.sessionID).toBe("sid-123");
    expect(spy).toHaveBeenCalledWith(
      expect.anything(),
      "jane@example.com",
      crypto.createHash("sha256").update("top-secret", "utf8").digest("hex")
    );
  });

  test("login wrong credentials", async () => {
    const app = createApp({
      db: {},
      queries: buildQueries({ accountLogin: async () => null })
    });

    const res = await request(app)
      .post("/login")
      .send({ email: "jane@example.com", password: "wrong" });

    expect(res.statusCode).toBe(400);
    expect(res.body.message).toContain("wrong credentials");
  });

  test("register success", async () => {
    const app = createApp({
      db: {},
      queries: buildQueries({
        insertUser: async () => 77,
        insertSession: async () => "sid-777"
      })
    });

    const res = await request(app).post("/register").send({
      name: "Ana",
      surname: "Smith",
      email: "ana@example.com",
      password: "safe-pass"
    });

    expect(res.statusCode).toBe(201);
    expect(res.body.message).toBe("successful registration");
    expect(res.body.sessionID).toBe("sid-777");
  });

  test("session login invalid session", async () => {
    const app = createApp({
      db: {},
      queries: buildQueries({ fetchSessionData: async () => null })
    });

    const res = await request(app).post("/session-login").send({ sessionID: "missing" });
    expect(res.statusCode).toBe(401);
    expect(res.body.message).toContain("invalid session");
  });

  test("register validation error", async () => {
    const app = createApp({ db: {}, queries: buildQueries() });
    const res = await request(app).post("/register").send({ name: "OnlyName" });
    expect(res.statusCode).toBe(422);
  });

  test("returns 503 when database is unavailable", async () => {
    const app = createApp({ db: null, queries: buildQueries() });
    const res = await request(app)
      .post("/login")
      .send({ email: "jane@example.com", password: "secret" });

    expect(res.statusCode).toBe(503);
  });
});
