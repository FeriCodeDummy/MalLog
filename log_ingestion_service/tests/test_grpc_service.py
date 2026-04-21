import json
import unittest

from contracts import log_ingestion_pb2
from services.grpc_service import LogIngestionService


class _AsyncChunkIterator:
    def __init__(self, chunks):
        self._chunks = chunks
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


class TestLogIngestionGrpcService(unittest.IsolatedAsyncioTestCase):
    async def test_upload_log_success(self):
        service = LogIngestionService(max_upload_bytes=1024 * 1024)
        line = (
            '127.0.0.1 - - [30/Mar/2026:14:22:01 +0200] "GET /index.html HTTP/1.1" '
            '200 612 "-" "Mozilla/5.0"'
        )
        payload = line.encode("utf-8")
        chunks = [
            log_ingestion_pb2.LogChunk(content=payload[:20]),
            log_ingestion_pb2.LogChunk(content=payload[20:]),
        ]

        response = await service.UploadLog(_AsyncChunkIterator(chunks), context=None)

        self.assertTrue(response.success)
        self.assertEqual(response.detected_log_type, "http_access_common")
        self.assertEqual(response.entry_count, 1)
        normalized = json.loads(response.normalized_logs_json)
        self.assertEqual(len(normalized["entries"]), 1)
        self.assertEqual(normalized["entries"][0]["log_type"], "http_access_common")

    async def test_upload_log_rejects_oversized_payload(self):
        service = LogIngestionService(max_upload_bytes=4)
        chunks = [log_ingestion_pb2.LogChunk(content=b"12345")]

        response = await service.UploadLog(_AsyncChunkIterator(chunks), context=None)

        self.assertFalse(response.success)
        self.assertIn("size limit", response.message)
        self.assertEqual(response.normalized_logs_json, "")

    async def test_upload_log_rejects_empty_stream(self):
        service = LogIngestionService(max_upload_bytes=1024)
        chunks = [log_ingestion_pb2.LogChunk(content=b"")]

        response = await service.UploadLog(_AsyncChunkIterator(chunks), context=None)

        self.assertFalse(response.success)
        self.assertEqual(response.message, "No .log file content received.")

    async def test_upload_log_rejects_non_utf8_payload(self):
        service = LogIngestionService(max_upload_bytes=1024)
        chunks = [log_ingestion_pb2.LogChunk(content=b"\xff\xfe\xfa")]

        response = await service.UploadLog(_AsyncChunkIterator(chunks), context=None)

        self.assertFalse(response.success)
        self.assertEqual(response.message, "Uploaded stream is not valid UTF-8 text.")

    async def test_upload_log_rejects_unsupported_format(self):
        service = LogIngestionService(max_upload_bytes=1024)
        unsupported = "[INFO] [07/02/2024 09:42:48] unsupported old format"
        chunks = [log_ingestion_pb2.LogChunk(content=unsupported.encode("utf-8"))]

        response = await service.UploadLog(_AsyncChunkIterator(chunks), context=None)

        self.assertFalse(response.success)
        self.assertIn("Unsupported log format", response.message)


if __name__ == "__main__":
    unittest.main()
