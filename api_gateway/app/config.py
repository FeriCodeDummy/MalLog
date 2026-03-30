import os
from dataclasses import dataclass


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _read_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _read_list_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return default
    values = [value.strip() for value in raw.split(",") if value.strip()]
    return values or default


@dataclass(frozen=True)
class Settings:
    http_host: str
    http_port: int
    test_log_path: str
    grpc_target: str
    grpc_chunk_size: int
    grpc_timeout_seconds: float
    rabbitmq_url: str
    anomaly_request_queue: str
    rabbitmq_timeout_seconds: float
    rabbitmq_poll_interval_seconds: float
    cassandra_contact_points: list[str]
    cassandra_port: int
    cassandra_keyspace: str
    cassandra_table: str


settings = Settings(
    http_host=os.getenv("API_GATEWAY_HTTP_HOST", "0.0.0.0"),
    http_port=_read_int_env("API_GATEWAY_HTTP_PORT", 8080),
    test_log_path=os.getenv("API_GATEWAY_TEST_LOG_PATH", "./system_test"),
    grpc_target=os.getenv("LOG_INGESTION_GRPC_TARGET", "localhost:50051"),
    grpc_chunk_size=_read_int_env("API_GATEWAY_GRPC_CHUNK_SIZE", 4096),
    grpc_timeout_seconds=_read_float_env("API_GATEWAY_GRPC_TIMEOUT_SECONDS", 20.0),
    rabbitmq_url=os.getenv("API_GATEWAY_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
    anomaly_request_queue=os.getenv("API_GATEWAY_ANOMALY_REQUEST_QUEUE", "anomaly.requests"),
    rabbitmq_timeout_seconds=_read_float_env("API_GATEWAY_RABBITMQ_TIMEOUT_SECONDS", 30.0),
    rabbitmq_poll_interval_seconds=_read_float_env(
        "API_GATEWAY_RABBITMQ_POLL_INTERVAL_SECONDS", 0.25
    ),
    cassandra_contact_points=_read_list_env(
        "API_GATEWAY_CASSANDRA_CONTACT_POINTS",
        ["localhost"],
    ),
    cassandra_port=_read_int_env("API_GATEWAY_CASSANDRA_PORT", 9042),
    cassandra_keyspace=os.getenv("API_GATEWAY_CASSANDRA_KEYSPACE", "gateway_logs"),
    cassandra_table=os.getenv("API_GATEWAY_CASSANDRA_TABLE", "call_logs"),
)
