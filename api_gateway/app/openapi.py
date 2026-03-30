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
