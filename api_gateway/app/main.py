import json
import atexit
from pathlib import Path
from typing import Any
from uuid import uuid4

import grpc
import pika
from flask import Flask, jsonify

from app.config import settings
from app.grpc_client import LogIngestionGrpcClient
from app.openapi import OPENAPI_SPEC
from app.rabbitmq_client import RabbitMQGatewayClient, RabbitMQRequestTimeoutError


def _build_default_cassandra_logger() -> Any:
    from app.cassandra_logger import CassandraLogRepository

    return CassandraLogRepository(
        contact_points=settings.cassandra_contact_points,
        port=settings.cassandra_port,
        keyspace=settings.cassandra_keyspace,
        table=settings.cassandra_table,
    )


def create_app(
    *,
    ingestion_client: LogIngestionGrpcClient | None = None,
    rabbitmq_client: RabbitMQGatewayClient | None = None,
    test_log_path: str | None = None,
    cassandra_logger: Any | None = None,
) -> Flask:
    app = Flask(__name__)

    app.config["cassandra_logger"] = cassandra_logger or _build_default_cassandra_logger()
    if hasattr(app.config["cassandra_logger"], "close"):
        atexit.register(app.config["cassandra_logger"].close)

    app.config["ingestion_client"] = ingestion_client or LogIngestionGrpcClient(
        target=settings.grpc_target,
        chunk_size=settings.grpc_chunk_size,
        timeout_seconds=settings.grpc_timeout_seconds,
        cassandra_logger=app.config["cassandra_logger"],
    )
    app.config["rabbitmq_client"] = rabbitmq_client or RabbitMQGatewayClient(
        amqp_url=settings.rabbitmq_url,
        request_queue=settings.anomaly_request_queue,
        timeout_seconds=settings.rabbitmq_timeout_seconds,
        poll_interval_seconds=settings.rabbitmq_poll_interval_seconds,
        cassandra_logger=app.config["cassandra_logger"],
    )
    app.config["openapi_spec"] = OPENAPI_SPEC
    app.config["test_log_path"] = test_log_path or settings.test_log_path

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/openapi.json")
    def openapi():
        return jsonify(app.config["openapi_spec"]), 200

    @app.get("/logs")
    def get_logs():
        try:
            logs = app.config["cassandra_logger"].read_logs()
        except Exception as exc:  # noqa: BLE001
            return jsonify({"message": f"Failed to fetch logs from Cassandra: {exc}"}), 503

        return jsonify({"count": len(logs), "logs": logs}), 200

    @app.get("/test")
    def run_system_test():
        configured_path = Path(app.config["test_log_path"])
        if not configured_path.exists():
            return (
                jsonify(
                    {
                        "message": (
                            f"Test log path not found: {configured_path}. "
                            "Expected './system_test' or './system_test/test.log'."
                        )
                    }
                ),
                500,
            )

        log_directory = configured_path.parent if configured_path.is_file() else configured_path
        log_files = sorted(path for path in log_directory.glob("*.log") if path.is_file())

        if not log_files:
            return (
                jsonify({"message": f"No .log files found in {log_directory}."}),
                400,
            )

        results: list[dict[str, object]] = []
        anomaly_detection_responses: list[dict[str, object]] = []
        successful_files = 0

        # Process strictly one by one (sequentially), not in parallel.
        for log_file in log_files:
            file_result: dict[str, object] = {"file_name": log_file.name}
            log_content = log_file.read_bytes()

            if not log_content:
                file_result["status"] = "failed"
                file_result["stage"] = "file_read"
                file_result["message"] = "Log file is empty."
                results.append(file_result)
                continue

            try:
                upload_result = app.config["ingestion_client"].upload_log(log_content)
            except grpc.RpcError as exc:
                file_result["status"] = "failed"
                file_result["stage"] = "log_ingestion_grpc"
                file_result["message"] = f"Failed to call log ingestion gRPC: {exc}"
                results.append(file_result)
                continue
            except Exception as exc:  # noqa: BLE001
                file_result["status"] = "failed"
                file_result["stage"] = "log_ingestion_grpc"
                file_result["message"] = f"Unexpected ingestion error: {exc}"
                results.append(file_result)
                continue

            if not upload_result.success:
                file_result["status"] = "failed"
                file_result["stage"] = "log_ingestion_validation"
                file_result["message"] = upload_result.message
                results.append(file_result)
                continue

            try:
                normalized_payload = json.loads(upload_result.normalized_logs_json)
            except json.JSONDecodeError:
                file_result["status"] = "failed"
                file_result["stage"] = "log_ingestion_normalization"
                file_result["message"] = "Log ingestion returned invalid normalized JSON."
                results.append(file_result)
                continue

            entries = normalized_payload.get("entries")
            if not isinstance(entries, list):
                file_result["status"] = "failed"
                file_result["stage"] = "log_ingestion_normalization"
                file_result["message"] = (
                    "Log ingestion response does not contain valid entries."
                )
                results.append(file_result)
                continue

            uid = uuid4().hex

            try:
                anomaly_result = app.config["rabbitmq_client"].request_anomaly_detection(
                    uid=uid,
                    entries=entries,
                )
            except RabbitMQRequestTimeoutError as exc:
                file_result["status"] = "failed"
                file_result["stage"] = "anomaly_detection_queue"
                file_result["uid"] = uid
                file_result["message"] = str(exc)
                results.append(file_result)
                continue
            except pika.exceptions.AMQPError as exc:
                file_result["status"] = "failed"
                file_result["stage"] = "anomaly_detection_queue"
                file_result["uid"] = uid
                file_result["message"] = f"RabbitMQ error: {exc}"
                results.append(file_result)
                continue
            except Exception as exc:  # noqa: BLE001
                file_result["status"] = "failed"
                file_result["stage"] = "anomaly_detection_queue"
                file_result["uid"] = uid
                file_result["message"] = f"Unexpected anomaly pipeline error: {exc}"
                results.append(file_result)
                continue

            successful_files += 1
            file_result["status"] = "success"
            file_result["uid"] = uid
            file_result["log_ingestion"] = {
                "message": upload_result.message,
                "detected_log_type": upload_result.detected_log_type,
                "entry_count": upload_result.entry_count,
            }
            file_result["anomaly_detection"] = anomaly_result
            anomaly_detection_responses.append(
                {
                    "file_name": log_file.name,
                    "uid": uid,
                    "response": anomaly_result,
                }
            )
            results.append(file_result)

        return jsonify(
            {
                "processed_files": len(log_files),
                "successful_files": successful_files,
                "failed_files": len(log_files) - successful_files,
                "anomaly_detection_responses": anomaly_detection_responses,
                "results": results,
                "processing_mode": "sequential",
                "order": [path.name for path in log_files],
            }
        ), 200

    return app
