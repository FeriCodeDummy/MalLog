import json
import time
from datetime import datetime, timezone
from typing import Any

import pika

from app.decorators import log_gateway_call


class RabbitMQRequestTimeoutError(TimeoutError):
    pass


class RabbitMQGatewayClient:
    def __init__(
        self,
        *,
        amqp_url: str,
        request_queue: str,
        timeout_seconds: float,
        poll_interval_seconds: float,
        cassandra_logger: Any | None = None,
    ) -> None:
        self._parameters = pika.URLParameters(amqp_url)
        self._request_queue = request_queue
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._cassandra_logger = cassandra_logger

    @log_gateway_call(destination="anomaly_detection_service", action="request_anomaly")
    def request_anomaly_detection(
        self,
        *,
        uid: str,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        connection = pika.BlockingConnection(self._parameters)
        channel = connection.channel()

        try:
            channel.queue_declare(queue=self._request_queue, durable=True)

            reply_queue = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
            reply_queue_name = reply_queue.method.queue

            channel.basic_publish(
                exchange="",
                routing_key=self._request_queue,
                body=json.dumps(
                    {
                        "uid": uid,
                        "entries": entries,
                        "queued_at": datetime.now(timezone.utc).isoformat(),
                        "reply_queue": reply_queue_name,
                    },
                    ensure_ascii=False,
                ).encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )

            deadline = time.monotonic() + self._timeout_seconds
            while time.monotonic() < deadline:
                method, _, body = channel.basic_get(queue=reply_queue_name, auto_ack=True)
                if method is None:
                    time.sleep(self._poll_interval_seconds)
                    continue

                try:
                    payload = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                if payload.get("uid") == uid:
                    return payload

            raise RabbitMQRequestTimeoutError(
                f"Timed out waiting for anomaly result for uid '{uid}'."
            )
        finally:
            connection.close()
