import unittest

from app.main import create_app


class FakeCoordinator:
    def __init__(self) -> None:
        self.jobs: dict[str, dict] = {}
        self.last_submitted_entries: list[dict] | None = None

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def submit_job(self, *, entries, uid=None):
        self.last_submitted_entries = entries
        job_uid = uid or "generated-uid"
        self.jobs[job_uid] = {
            "uid": job_uid,
            "started_at": "2026-03-30T10:00:00",
            "ended_at": "2026-03-30T10:00:01",
            "result": {"label": "NORMAL", "score": 0.2},
        }
        return job_uid

    def get_job(self, uid):
        return self.jobs.get(uid)


class TestAnomalyApi(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = FakeCoordinator()
        app = create_app(coordinator=self.coordinator, start_background_workers=False)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_openapi_endpoint(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["openapi"], "3.0.3")
        self.assertIn("/api/v1/anomaly/jobs", body["paths"])

    def test_submit_job_success(self):
        response = self.client.post(
            "/api/v1/anomaly/jobs",
            json={
                "entries": [
                    {
                        "log_type": "http_access_common",
                        "raw_line": '127.0.0.1 - - [30/Mar/2026:14:22:01 +0200] "GET / HTTP/1.1" 200 612 "-" "Mozilla/5.0"',
                        "timestamp": "2026-03-30T10:00:00",
                        "message": "GET /",
                        "severity": "info",
                        "parsed_fields": {"status": "200"},
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 202)
        body = response.get_json()
        self.assertEqual(body["status"], "queued")
        self.assertEqual(body["uid"], "generated-uid")

    def test_submit_job_rejects_invalid_payload(self):
        response = self.client.post("/api/v1/anomaly/jobs", json={"entries": []})
        self.assertEqual(response.status_code, 400)

    def test_fetch_job_pending(self):
        response = self.client.get("/api/v1/anomaly/jobs/unknown")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "pending")

    def test_fetch_job_completed(self):
        self.coordinator.jobs["abc123"] = {
            "uid": "abc123",
            "started_at": "2026-03-30T10:00:00",
            "ended_at": "2026-03-30T10:00:05",
            "result": {"label": "ANOMALY", "score": 0.9},
        }

        response = self.client.get("/api/v1/anomaly/jobs/abc123")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["result"]["label"], "ANOMALY")


if __name__ == "__main__":
    unittest.main()
