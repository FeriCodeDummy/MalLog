import json

import grpc

from contracts import log_ingestion_pb2, log_ingestion_pb2_grpc
from services.log_parser import LogFormatError, detect_and_normalize_log


class LogIngestionService(log_ingestion_pb2_grpc.LogIngestionServiceServicer):
    def __init__(self, max_upload_bytes: int) -> None:
        self._max_upload_bytes = max_upload_bytes

    async def UploadLog(
        self,
        request_iterator,
        context,  # noqa: ARG002 - required gRPC method signature
    ) -> log_ingestion_pb2.UploadResponse:
        payload = bytearray()
        chunks_received = 0

        async for chunk in request_iterator:
            if not chunk.content:
                continue

            chunks_received += 1
            payload.extend(chunk.content)

            if len(payload) > self._max_upload_bytes:
                return log_ingestion_pb2.UploadResponse(
                    success=False,
                    message=(
                        f"Upload exceeds configured size limit of "
                        f"{self._max_upload_bytes} bytes."
                    ),
                    normalized_logs_json="",
                )

        if not payload:
            return log_ingestion_pb2.UploadResponse(
                success=False,
                message="No .log file content received.",
                normalized_logs_json="",
            )

        try:
            content = payload.decode("utf-8")
        except UnicodeDecodeError:
            return log_ingestion_pb2.UploadResponse(
                success=False,
                message="Uploaded stream is not valid UTF-8 text.",
                normalized_logs_json="",
            )

        try:
            parse_result = detect_and_normalize_log(content)
        except LogFormatError as exc:
            return log_ingestion_pb2.UploadResponse(
                success=False,
                message=str(exc),
                normalized_logs_json="",
            )

        normalized_json = json.dumps(parse_result.to_payload(), ensure_ascii=False)

        return log_ingestion_pb2.UploadResponse(
            success=True,
            message=(
                f"Successfully ingested {len(parse_result.entries)} entries from "
                f"{chunks_received} chunk(s)."
            ),
            normalized_logs_json=normalized_json,
            detected_format=parse_result.detected_format,
            entry_count=len(parse_result.entries),
        )


class GrpcServerManager:
    def __init__(self, host: str, port: int, max_upload_bytes: int) -> None:
        self._server = grpc.aio.server()
        self._started = False

        log_ingestion_pb2_grpc.add_LogIngestionServiceServicer_to_server(
            LogIngestionService(max_upload_bytes=max_upload_bytes), self._server
        )
        self._server.add_insecure_port(f"{host}:{port}")

    async def start(self) -> None:
        if self._started:
            return
        await self._server.start()
        self._started = True

    async def stop(self, grace: float = 3.0) -> None:
        if not self._started:
            return
        await self._server.stop(grace)
        self._started = False
