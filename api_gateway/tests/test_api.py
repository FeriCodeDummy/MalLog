import json
import unittest
from pathlib import Path
from uuid import uuid4

from app.grpc_client import IngestionUploadResult
from app.main import create_app
from app.rabbitmq_client import RabbitMQRequestTimeoutError


class FakeIngestionClient:
    def __init__(self, responses: list[IngestionUploadResult]) -> None:
        self.responses = responses
        self.called_payloads: list[bytes] = []

    def upload_log(self, content: bytes) -> IngestionUploadResult:
        self.called_payloads.append(content)
        index = min(len(self.called_payloads) - 1, len(self.responses) - 1)
        return self.responses[index]


class FakeRabbitClient:
    def __init__(self, should_timeout: bool = False) -> None:
        self.should_timeout = should_timeout
        self.calls: list[dict] = []

    def request_anomaly_detection(self, *, uid: str, entries: list[dict]):
        self.calls.append({"uid": uid, "entries": entries})
        if self.should_timeout:
            raise RabbitMQRequestTimeoutError("Timed out waiting for anomaly result.")
        return {"uid": uid, "result": {"label": "ANOMALY", "score": 0.9}}


class FakeCassandraLogger:
    def __init__(self) -> None:
        self._logs = [
            {
                "id": "f0000000-0000-0000-0000-000000000001",
                "source": "api_gateway",
                "destination": "log_ingestion_service",
                "action": "upload_log:request",
                "timestamp": "2026-03-30T18:00:00+00:00",
            }
        ]

    def safe_write_log(self, **_kwargs):
        return None

    def read_logs(self):
        return list(self._logs)

    def close(self):
        return None


class TestApiGateway(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_files: list[Path] = []
        self._tmp_dirs: list[Path] = []

    def tearDown(self) -> None:
        for path in self._tmp_files:
            if path.exists():
                path.unlink()

        for directory in self._tmp_dirs:
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()

    def _create_log_dir(self) -> Path:
        tmp_dir = Path(__file__).parent / ".tmp" / uuid4().hex
        tmp_dir.mkdir(parents=True, exist_ok=True)
        self._tmp_dirs.append(tmp_dir)
        return tmp_dir

    def _create_log_file(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content, encoding="utf-8")
        self._tmp_files.append(path)
        return path

    def _make_app(
        self,
        *,
        test_log_path: str,
        responses: list[IngestionUploadResult],
        should_timeout: bool = False,
    ):
        ingestion = FakeIngestionClient(responses)
        rabbit = FakeRabbitClient(should_timeout=should_timeout)
        cassandra_logger = FakeCassandraLogger()
        app = create_app(
            ingestion_client=ingestion,
            rabbitmq_client=rabbit,
            test_log_path=test_log_path,
            cassandra_logger=cassandra_logger,
        )
        app.config["TESTING"] = True
        return app, ingestion, rabbit, cassandra_logger

    def _success_response(self) -> IngestionUploadResult:
        return IngestionUploadResult(
            success=True,
            message="ingested",
            normalized_logs_json=json.dumps(
                {
                    "entries": [
                        {
                            "log_type": "http_access_common",
                            "raw_line": "line",
                            "timestamp": "2026-03-30T10:00:00",
                            "message": "GET /",
                            "severity": "info",
                            "parsed_fields": {"status": "200"},
                        }
                    ]
                }
            ),
            detected_log_type="http_access_common",
            entry_count=1,
        )

    def test_health(self):
        app, _, _, _ = self._make_app(
            test_log_path="missing",
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_openapi(self):
        app, _, _, _ = self._make_app(
            test_log_path="missing",
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/test", response.get_json()["paths"])

    def test_test_endpoint_processes_all_files_sequentially(self):
        log_dir = self._create_log_dir()
        a_content = "A sample line"
        b_content = "B sample line"
        self._create_log_file(log_dir, "b.log", b_content)
        self._create_log_file(log_dir, "a.log", a_content)

        app, ingestion, rabbit, _ = self._make_app(
            test_log_path=str(log_dir),
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)

        body = response.get_json()
        self.assertEqual(body["processing_mode"], "sequential")
        self.assertEqual(body["order"], ["a.log", "b.log"])
        self.assertEqual(body["processed_files"], 2)
        self.assertEqual(body["successful_files"], 2)
        self.assertEqual(body["failed_files"], 0)
        self.assertEqual(len(body["anomaly_detection_responses"]), 2)
        self.assertEqual(
            [item["file_name"] for item in body["anomaly_detection_responses"]],
            ["a.log", "b.log"],
        )
        self.assertTrue(
            all(
                item["response"]["result"]["label"] == "ANOMALY"
                for item in body["anomaly_detection_responses"]
            )
        )
        self.assertEqual(ingestion.called_payloads, [a_content.encode(), b_content.encode()])
        self.assertEqual(len(rabbit.calls), 2)

    def test_test_endpoint_processes_all_files_before_returning_aggregated_anomaly_responses(self):
        log_dir = self._create_log_dir()
        self._create_log_file(log_dir, "b.log", "B sample line")
        self._create_log_file(log_dir, "a.log", "A sample line")
        failure_response = IngestionUploadResult(
            success=False,
            message="unsupported format",
            normalized_logs_json="",
            detected_log_type="",
            entry_count=0,
        )
        app, _, rabbit, _ = self._make_app(
            test_log_path=str(log_dir),
            responses=[self._success_response(), failure_response],
        )

        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)

        body = response.get_json()
        self.assertEqual(body["processed_files"], 2)
        self.assertEqual(body["successful_files"], 1)
        self.assertEqual(body["failed_files"], 1)
        self.assertEqual(len(rabbit.calls), 1)
        self.assertEqual(len(body["anomaly_detection_responses"]), 1)
        self.assertEqual(body["anomaly_detection_responses"][0]["file_name"], "a.log")
        self.assertEqual(body["results"][1]["file_name"], "b.log")
        self.assertEqual(body["results"][1]["stage"], "log_ingestion_validation")

    def test_test_endpoint_missing_path(self):
        app, _, _, _ = self._make_app(
            test_log_path="not-existing-path",
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 500)

    def test_test_endpoint_no_logs(self):
        empty_dir = self._create_log_dir()
        app, _, _, _ = self._make_app(
            test_log_path=str(empty_dir),
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 400)

    def test_test_endpoint_ingestion_failure_is_reported(self):
        log_dir = self._create_log_dir()
        self._create_log_file(log_dir, "only.log", "x")
        failure_response = IngestionUploadResult(
            success=False,
            message="unsupported format",
            normalized_logs_json="",
            detected_log_type="",
            entry_count=0,
        )
        app, _, _, _ = self._make_app(
            test_log_path=str(log_dir),
            responses=[failure_response],
        )
        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["failed_files"], 1)
        self.assertEqual(body["anomaly_detection_responses"], [])
        self.assertEqual(body["results"][0]["stage"], "log_ingestion_validation")

    def test_test_endpoint_timeout_is_reported(self):
        log_dir = self._create_log_dir()
        self._create_log_file(log_dir, "only.log", "x")
        app, _, _, _ = self._make_app(
            test_log_path=str(log_dir),
            responses=[self._success_response()],
            should_timeout=True,
        )
        client = app.test_client()
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["failed_files"], 1)
        self.assertEqual(body["anomaly_detection_responses"], [])
        self.assertEqual(body["results"][0]["stage"], "anomaly_detection_queue")

    def test_logs_endpoint(self):
        app, _, _, cassandra_logger = self._make_app(
            test_log_path="missing",
            responses=[self._success_response()],
        )
        client = app.test_client()
        response = client.get("/logs")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["logs"][0]["action"], "upload_log:request")
        self.assertEqual(len(cassandra_logger.read_logs()), 1)


if __name__ == "__main__":
    unittest.main()
