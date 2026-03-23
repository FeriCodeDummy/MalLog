# -*- coding: utf-8 -*-
"""Protocol buffer classes for log ingestion gRPC contract.

This module mirrors generated protobuf output and is kept in-repo so the
service can run without requiring protoc at runtime.
"""

from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()


def _build_file_descriptor() -> _descriptor_pb2.FileDescriptorProto:
    file_descriptor = _descriptor_pb2.FileDescriptorProto()
    file_descriptor.name = "contracts/log_ingestion.proto"
    file_descriptor.package = "logingestion"
    file_descriptor.syntax = "proto3"

    log_chunk = file_descriptor.message_type.add()
    log_chunk.name = "LogChunk"
    log_chunk_content = log_chunk.field.add()
    log_chunk_content.name = "content"
    log_chunk_content.number = 1
    log_chunk_content.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    log_chunk_content.type = _descriptor_pb2.FieldDescriptorProto.TYPE_BYTES

    upload_response = file_descriptor.message_type.add()
    upload_response.name = "UploadResponse"

    response_success = upload_response.field.add()
    response_success.name = "success"
    response_success.number = 1
    response_success.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    response_success.type = _descriptor_pb2.FieldDescriptorProto.TYPE_BOOL

    response_message = upload_response.field.add()
    response_message.name = "message"
    response_message.number = 2
    response_message.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    response_message.type = _descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    response_payload = upload_response.field.add()
    response_payload.name = "normalized_logs_json"
    response_payload.number = 3
    response_payload.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    response_payload.type = _descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    response_detected_format = upload_response.field.add()
    response_detected_format.name = "detected_format"
    response_detected_format.number = 4
    response_detected_format.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    response_detected_format.type = _descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    response_entry_count = upload_response.field.add()
    response_entry_count.name = "entry_count"
    response_entry_count.number = 5
    response_entry_count.label = _descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    response_entry_count.type = _descriptor_pb2.FieldDescriptorProto.TYPE_INT32

    service = file_descriptor.service.add()
    service.name = "LogIngestionService"

    method = service.method.add()
    method.name = "UploadLog"
    method.input_type = ".logingestion.LogChunk"
    method.output_type = ".logingestion.UploadResponse"
    method.client_streaming = True

    return file_descriptor


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    _build_file_descriptor().SerializeToString()
)

_LOGCHUNK = DESCRIPTOR.message_types_by_name["LogChunk"]
_UPLOADRESPONSE = DESCRIPTOR.message_types_by_name["UploadResponse"]

LogChunk = _reflection.GeneratedProtocolMessageType(
    "LogChunk",
    (_message.Message,),
    {
        "DESCRIPTOR": _LOGCHUNK,
        "__module__": "contracts.log_ingestion_pb2",
    },
)
_sym_db.RegisterMessage(LogChunk)

UploadResponse = _reflection.GeneratedProtocolMessageType(
    "UploadResponse",
    (_message.Message,),
    {
        "DESCRIPTOR": _UPLOADRESPONSE,
        "__module__": "contracts.log_ingestion_pb2",
    },
)
_sym_db.RegisterMessage(UploadResponse)

__all__ = [
    "LogChunk",
    "UploadResponse",
]
