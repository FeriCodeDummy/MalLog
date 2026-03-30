"""gRPC helpers for log ingestion contract."""

import grpc

from contracts import log_ingestion_pb2 as log__ingestion__pb2


class LogIngestionServiceStub:
    """Client stub for LogIngestionService."""

    def __init__(self, channel: grpc.Channel) -> None:
        self.UploadLog = channel.stream_unary(
            "/logingestion.LogIngestionService/UploadLog",
            request_serializer=log__ingestion__pb2.LogChunk.SerializeToString,
            response_deserializer=log__ingestion__pb2.UploadResponse.FromString,
        )


class LogIngestionServiceServicer:
    """Server API for LogIngestionService."""

    async def UploadLog(self, request_iterator, context):  # noqa: N802
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented.")
        raise NotImplementedError("UploadLog is not implemented.")


def add_LogIngestionServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "UploadLog": grpc.stream_unary_rpc_method_handler(
            servicer.UploadLog,
            request_deserializer=log__ingestion__pb2.LogChunk.FromString,
            response_serializer=log__ingestion__pb2.UploadResponse.SerializeToString,
        )
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "logingestion.LogIngestionService",
        rpc_method_handlers,
    )
    server.add_generic_rpc_handlers((generic_handler,))
