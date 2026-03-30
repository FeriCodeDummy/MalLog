from dataclasses import dataclass
from typing import Any

import grpc

from app.decorators import log_gateway_call
from contracts import log_ingestion_pb2, log_ingestion_pb2_grpc


@dataclass(frozen=True)
class IngestionUploadResult:
    success: bool
    message: str
    normalized_logs_json: str
    detected_log_type: str
    entry_count: int


class LogIngestionGrpcClient:
    def __init__(
        self,
        *,
        target: str,
        chunk_size: int,
        timeout_seconds: float,
        max_message_bytes: int,
        cassandra_logger: Any | None = None,
    ) -> None:
        self._target = target
        self._chunk_size = chunk_size
        self._timeout_seconds = timeout_seconds
        self._max_message_bytes = max_message_bytes
        self._cassandra_logger = cassandra_logger

    @log_gateway_call(destination="log_ingestion_service", action="upload_log")
    def upload_log(self, content: bytes) -> IngestionUploadResult:
        if not content:
            raise ValueError("No log content provided.")

        with grpc.insecure_channel(
            self._target,
            options=[
                ("grpc.max_send_message_length", self._max_message_bytes),
                ("grpc.max_receive_message_length", self._max_message_bytes),
            ],
        ) as channel:
            stub = log_ingestion_pb2_grpc.LogIngestionServiceStub(channel)

            def request_iterator():
                for index in range(0, len(content), self._chunk_size):
                    yield log_ingestion_pb2.LogChunk(
                        content=content[index : index + self._chunk_size]
                    )

            response = stub.UploadLog(request_iterator(), timeout=self._timeout_seconds)

        return IngestionUploadResult(
            success=response.success,
            message=response.message,
            normalized_logs_json=response.normalized_logs_json,
            detected_log_type=response.detected_log_type,
            entry_count=response.entry_count,
        )
