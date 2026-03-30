OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Anomaly Detection Service API",
        "version": "1.0.0",
        "description": (
            "Consumes normalized logs asynchronously through RabbitMQ, runs anomaly "
            "detection, stores results in MySQL, and publishes result events back "
            "to RabbitMQ."
        ),
    },
    "paths": {
        "/health": {
            "get": {
                "summary": "Service health",
                "responses": {
                    "200": {
                        "description": "Service is alive",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"},
                            }
                        },
                    }
                },
            }
        },
        "/openapi.json": {
            "get": {
                "summary": "OpenAPI specification",
                "responses": {
                    "200": {
                        "description": "OpenAPI document",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/api/v1/anomaly/jobs": {
            "post": {
                "summary": "Queue anomaly detection job",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AnomalyJobRequest"}
                        }
                    },
                },
                "responses": {
                    "202": {
                        "description": "Job queued",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueuedResponse"}
                            }
                        },
                    },
                    "400": {
                        "description": "Validation error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            }
        },
        "/api/v1/anomaly/jobs/{uid}": {
            "get": {
                "summary": "Fetch anomaly detection result",
                "parameters": [
                    {
                        "in": "path",
                        "name": "uid",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Pending or completed result",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JobStatusResponse"}
                            }
                        },
                    }
                },
            }
        },
    },
    "components": {
        "schemas": {
            "LogEntry": {
                "type": "object",
                "required": ["log_type", "raw_line", "message"],
                "properties": {
                    "log_type": {"type": "string"},
                    "raw_line": {"type": "string"},
                    "message": {"type": "string"},
                    "timestamp": {"type": "string", "nullable": True},
                    "severity": {"type": "string", "nullable": True},
                    "parsed_fields": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                },
            },
            "AnomalyJobRequest": {
                "type": "object",
                "required": ["entries"],
                "properties": {
                    "uid": {"type": "string"},
                    "entries": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/LogEntry"},
                    },
                },
            },
            "QueuedResponse": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string"},
                    "status": {"type": "string", "example": "queued"},
                },
            },
            "JobStatusResponse": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string"},
                    "status": {"type": "string", "example": "completed"},
                    "started_at": {"type": "string"},
                    "ended_at": {"type": "string"},
                    "result": {"type": "object"},
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
            },
        }
    },
}
