import unittest

from app.coordinator import AnomalyCoordinator


class FakeRepository:
    def __init__(self) -> None:
        self.saved: list[dict] = []
        self.by_uid: dict[str, dict] = {}

    def save_detection(self, *, uid, started_at, ended_at, result):
        record = {
            "uid": uid,
            "started_at": started_at.isoformat() + "Z",
            "ended_at": ended_at.isoformat() + "Z",
            "result": result,
        }
        self.saved.append(record)
        self.by_uid[uid] = record

    def get_detection(self, uid):
        return self.by_uid.get(uid)


class FakeRabbitMq:
    def __init__(self) -> None:
        self.consumer_callback = None
        self.stopped = False
        self.requests: list[dict] = []
        self.results: list[dict] = []

    def start_request_consumer(self, callback):
        self.consumer_callback = callback

    def stop(self):
        self.stopped = True

    def publish_request(self, payload):
        self.requests.append(payload)

    def publish_result(self, payload, queue=None):
        self.results.append({"payload": payload, "queue": queue})


class TestAnomalyCoordinator(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeRepository()
        self.rabbitmq = FakeRabbitMq()
        self.coordinator = AnomalyCoordinator(
            repository=self.repository,
            rabbitmq=self.rabbitmq,
        )

    def test_start_and_stop_delegate_to_rabbitmq(self):
        self.coordinator.start()
        self.assertIsNotNone(self.rabbitmq.consumer_callback)

        self.coordinator.stop()
        self.assertTrue(self.rabbitmq.stopped)

    def test_submit_job_uses_provided_uid_and_publishes_request(self):
        uid = self.coordinator.submit_job(entries=[{"message": "x"}], uid="job-123")

        self.assertEqual(uid, "job-123")
        self.assertEqual(len(self.rabbitmq.requests), 1)
        payload = self.rabbitmq.requests[0]
        self.assertEqual(payload["uid"], "job-123")
        self.assertEqual(payload["entries"], [{"message": "x"}])
        self.assertIn("queued_at", payload)

    def test_get_job_reads_from_repository(self):
        self.repository.by_uid["abc"] = {
            "uid": "abc",
            "started_at": "2026-03-30T10:00:00Z",
            "ended_at": "2026-03-30T10:00:01Z",
            "result": {"label": "NORMAL", "score": 0.1},
        }

        result = self.coordinator.get_job("abc")

        self.assertIsNotNone(result)
        self.assertEqual(result["uid"], "abc")

    def test_handle_request_message_saves_and_publishes_result(self):
        payload = {
            "uid": "req-1",
            "entries": [
                {
                    "log_type": "nginx_error",
                    "raw_line": "x",
                    "message": "failed login",
                    "severity": "error",
                    "timestamp": "2026-03-30T10:00:00",
                    "parsed_fields": {},
                }
            ],
            "reply_queue": "gateway.replies",
        }

        self.coordinator._handle_request_message(payload)

        self.assertEqual(len(self.repository.saved), 1)
        self.assertEqual(self.repository.saved[0]["uid"], "req-1")
        self.assertEqual(len(self.rabbitmq.results), 1)
        self.assertEqual(self.rabbitmq.results[0]["queue"], "gateway.replies")
        self.assertEqual(self.rabbitmq.results[0]["payload"]["uid"], "req-1")
        self.assertIn("result", self.rabbitmq.results[0]["payload"])


if __name__ == "__main__":
    unittest.main()
