import os
from dataclasses import dataclass


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    http_host: str
    http_port: int
    grpc_host: str
    grpc_port: int
    max_upload_bytes: int


settings = Settings(
    http_host=os.getenv("LOG_INGESTION_HTTP_HOST", "0.0.0.0"),
    http_port=_read_int_env("LOG_INGESTION_HTTP_PORT", 8001),
    grpc_host=os.getenv("LOG_INGESTION_GRPC_HOST", "0.0.0.0"),
    grpc_port=_read_int_env("LOG_INGESTION_GRPC_PORT", 50051),
    max_upload_bytes=_read_int_env("LOG_INGESTION_MAX_UPLOAD_BYTES", 10 * 1024 * 1024),
)
