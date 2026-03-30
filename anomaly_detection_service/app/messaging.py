import json
import threading
import time
from collections.abc import Callable
from typing import Any

import pika


class RabbitMQClient:
    def __init__(self, *, amqp_url: str, request_queue: str, result_queue: str) -> None:
        self._parameters = pika.URLParameters(amqp_url)
        self.request_queue = request_queue
        self.result_queue = result_queue
        self._stop_event = threading.Event()
        self._consumer_thread: threading.Thread | None = None

    def _connect(self):
        connection = pika.BlockingConnection(self._parameters)
        channel = connection.channel()
        channel.queue_declare(queue=self.request_queue, durable=True)
        channel.queue_declare(queue=self.result_queue, durable=True)
        return connection, channel

    def _publish(self, queue: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        last_error: Exception | None = None

        for _ in range(5):
            try:
                connection, channel = self._connect()
                try:
                    channel.basic_publish(
                        exchange="",
                        routing_key=queue,
                        body=body,
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type="application/json",
                        ),
                    )
                    return
                finally:
                    connection.close()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.5)

        raise RuntimeError(f"Unable to publish message to queue '{queue}'.") from last_error

    def publish_request(self, payload: dict[str, Any]) -> None:
        self._publish(self.request_queue, payload)

    def publish_result(self, payload: dict[str, Any], queue: str | None = None) -> None:
        self._publish(queue or self.result_queue, payload)

    def start_request_consumer(self, callback: Callable[[dict[str, Any]], None]) -> None:
        if self._consumer_thread is not None and self._consumer_thread.is_alive():
            return

        self._stop_event.clear()
        self._consumer_thread = threading.Thread(
            target=self._consume_loop,
            args=(callback,),
            daemon=True,
        )
        self._consumer_thread.start()

    def _consume_loop(self, callback: Callable[[dict[str, Any]], None]) -> None:
        while not self._stop_event.is_set():
            connection = None
            channel = None
            try:
                connection, channel = self._connect()
                for method, _, body in channel.consume(
                    queue=self.request_queue,
                    inactivity_timeout=1,
                    auto_ack=False,
                ):
                    if self._stop_event.is_set():
                        break
                    if method is None:
                        continue

                    try:
                        payload = json.loads(body.decode("utf-8"))
                        callback(payload)
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:  # noqa: BLE001
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                if channel is not None and channel.is_open:
                    channel.cancel()
            except Exception:  # noqa: BLE001
                if self._stop_event.is_set():
                    break
                time.sleep(2)
            finally:
                if connection is not None and connection.is_open:
                    connection.close()

    def stop(self) -> None:
        self._stop_event.set()
        if self._consumer_thread is not None:
            self._consumer_thread.join(timeout=5)
