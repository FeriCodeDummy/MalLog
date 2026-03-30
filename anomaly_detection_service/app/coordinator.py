from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.detection import run_anomaly_detection
from app.messaging import RabbitMQClient
from app.repository import DetectionRepository


class AnomalyCoordinator:
    def __init__(
        self,
        *,
        repository: DetectionRepository,
        rabbitmq: RabbitMQClient,
    ) -> None:
        self._repository = repository
        self._rabbitmq = rabbitmq

    def start(self) -> None:
        self._rabbitmq.start_request_consumer(self._handle_request_message)

    def stop(self) -> None:
        self._rabbitmq.stop()

    def submit_job(self, *, entries: list[dict[str, Any]], uid: str | None = None) -> str:
        job_uid = uid or uuid4().hex
        self._rabbitmq.publish_request(
            {
                "uid": job_uid,
                "entries": entries,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return job_uid

    def get_job(self, uid: str) -> dict[str, Any] | None:
        return self._repository.get_detection(uid)

    def _handle_request_message(self, payload: dict[str, Any]) -> None:
        uid = str(payload.get("uid") or uuid4().hex)
        entries = payload.get("entries")
        reply_queue = payload.get("reply_queue")
        reply_queue_name = (
            reply_queue.strip()
            if isinstance(reply_queue, str) and reply_queue.strip()
            else None
        )
        if not isinstance(entries, list):
            entries = []

        started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        detection_result = run_anomaly_detection(entries)
        ended_at = datetime.now(timezone.utc).replace(tzinfo=None)

        self._repository.save_detection(
            uid=uid,
            started_at=started_at,
            ended_at=ended_at,
            result=detection_result,
        )

        self._rabbitmq.publish_result(
            {
                "uid": uid,
                "started_at": started_at.isoformat() + "Z",
                "ended_at": ended_at.isoformat() + "Z",
                "result": detection_result,
            },
            queue=reply_queue_name,
        )
