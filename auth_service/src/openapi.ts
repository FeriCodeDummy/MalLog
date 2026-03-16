export const openApiSpec = {
  openapi: "3.0.3",
  info: {
    title: "Auth Service API",
    version: "1.0.0"
  },
  servers: [
    {
      url: "/"
    }
  ],
  paths: {
    "/login": {
      post: {
        summary: "Login user and create session",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["email", "password"],
                properties: {
                  email: { type: "string", format: "email" },
                  password: { type: "string" }
                }
              }
            }
          }
        },
        responses: {
          "200": { description: "Logged in" },
          "400": { description: "Wrong credentials" },
          "503": { description: "Database unavailable" }
        }
      }
    },
    "/session-login": {
      post: {
        summary: "Login with existing session",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["sessionID"],
                properties: {
                  sessionID: { type: "string" }
                }
              }
            }
          }
        },
        responses: {
          "200": { description: "Session valid" },
          "401": { description: "Invalid session" },
          "503": { description: "Database unavailable" }
        }
      }
    },
    "/register": {
      post: {
        summary: "Register user and create session",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["name", "surname", "email", "password"],
                properties: {
                  name: { type: "string" },
                  surname: { type: "string" },
                  email: { type: "string", format: "email" },
                  password: { type: "string" }
                }
              }
            }
          }
        },
        responses: {
          "201": { description: "Registered" },
          "400": { description: "Bad data" },
          "422": { description: "Validation error" },
          "503": { description: "Database unavailable" }
        }
      }
    },
    "/refresh-jwt": {
      post: {
        summary: "Refresh JWT token",
        responses: {
          "503": { description: "Not implemented" }
        }
      }
    },
    "/.well-known/jwks.json": {
      get: {
        summary: "JWK set endpoint",
        responses: {
          "503": { description: "Not implemented" }
        }
      }
    },
    "/health": {
      get: {
        summary: "Health check",
        responses: {
          "200": { description: "OK" }
        }
      }
    }
  }
};
