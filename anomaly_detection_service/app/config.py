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


@dataclass(frozen=True)
class Settings:
    http_host: str
    http_port: int
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    rabbitmq_url: str
    request_queue: str
    result_queue: str


settings = Settings(
    http_host=os.getenv("ANOMALY_HTTP_HOST", "0.0.0.0"),
    http_port=_read_int_env("ANOMALY_HTTP_PORT", 5002),
    mysql_host=os.getenv("ANOMALY_MYSQL_HOST", "localhost"),
    mysql_port=_read_int_env("ANOMALY_MYSQL_PORT", 3306),
    mysql_user=os.getenv("ANOMALY_MYSQL_USER", "app"),
    mysql_password=os.getenv("ANOMALY_MYSQL_PASSWORD", "ppa"),
    mysql_database=os.getenv("ANOMALY_MYSQL_DATABASE", "anomaly_detection"),
    rabbitmq_url=os.getenv("ANOMALY_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
    request_queue=os.getenv("ANOMALY_REQUEST_QUEUE", "anomaly.requests"),
    result_queue=os.getenv("ANOMALY_RESULT_QUEUE", "anomaly.results"),
)
