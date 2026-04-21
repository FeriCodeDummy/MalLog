OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "MalLog API Gateway",
        "version": "1.0.0",
        "description": (
            "Gateway endpoint that loads a local test log, forwards it to the log "
            "ingestion service over gRPC, then sends normalized entries to anomaly "
            "detection over RabbitMQ and returns the final detection result."
        ),
    },
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/openapi.json": {
            "get": {
                "summary": "OpenAPI document",
                "responses": {"200": {"description": "OpenAPI JSON"}},
            }
        },
        "/test": {
            "get": {
                "summary": (
                    "Run sequential end-to-end flow for all /system_test/*.log files "
                    "and return aggregated anomaly responses as JSON"
                ),
                "responses": {
                    "200": {"description": "Flow completed"},
                    "400": {"description": "No .log files found"},
                    "500": {"description": "Invalid system_test path"},
                },
            }
        },
        "/submit": {
            "post": {
                "summary": "Submit a single .log file and run end-to-end analysis",
                "responses": {
                    "200": {"description": "Flow completed"},
                    "400": {"description": "Missing file or invalid extension"},
                },
            }
        },
        "/login": {
            "post": {
                "summary": "Proxy login request to auth service",
                "responses": {
                    "200": {"description": "Logged in"},
                    "400": {"description": "Wrong credentials"},
                    "422": {"description": "Validation error"},
                    "503": {"description": "Auth service unavailable"},
                },
            }
        },
        "/register": {
            "post": {
                "summary": "Proxy registration request to auth service",
                "responses": {
                    "201": {"description": "Registered"},
                    "400": {"description": "Bad data"},
                    "422": {"description": "Validation error"},
                    "503": {"description": "Auth service unavailable"},
                },
            }
        },
        "/session-login": {
            "post": {
                "summary": "Proxy session validation request to auth service",
                "responses": {
                    "200": {"description": "Session valid"},
                    "400": {"description": "Missing session ID"},
                    "401": {"description": "Invalid session"},
                    "503": {"description": "Auth service unavailable"},
                },
            }
        },
        "/logs": {
            "get": {
                "summary": "Fetch gateway call logs from Cassandra",
                "responses": {
                    "200": {"description": "Logs fetched"},
                    "503": {"description": "Cassandra unavailable"},
                },
            }
        },
    },
}
