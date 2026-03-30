import atexit
from typing import Any

from flask import Flask, jsonify, request

from app.config import settings
from app.coordinator import AnomalyCoordinator
from app.messaging import RabbitMQClient
from app.openapi import OPENAPI_SPEC
from app.repository import DetectionRepository


def _build_default_coordinator() -> AnomalyCoordinator:
    repository = DetectionRepository(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
    )
    rabbitmq = RabbitMQClient(
        amqp_url=settings.rabbitmq_url,
        request_queue=settings.request_queue,
        result_queue=settings.result_queue,
    )
    return AnomalyCoordinator(repository=repository, rabbitmq=rabbitmq)


def _is_valid_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False

    log_type = entry.get("log_type")
    raw_line = entry.get("raw_line")
    message = entry.get("message")
    parsed_fields = entry.get("parsed_fields")

    if not isinstance(log_type, str) or not log_type:
        return False
    if not isinstance(raw_line, str) or not raw_line:
        return False
    if not isinstance(message, str) or not message:
        return False
    if parsed_fields is not None and not isinstance(parsed_fields, dict):
        return False

    return True


def create_app(
    *,
    coordinator: AnomalyCoordinator | Any | None = None,
    start_background_workers: bool = True,
) -> Flask:
    app = Flask(__name__)
    app.config["coordinator"] = coordinator or _build_default_coordinator()
    app.config["openapi_spec"] = OPENAPI_SPEC

    if start_background_workers:
        app.config["coordinator"].start()
        atexit.register(app.config["coordinator"].stop)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/openapi.json")
    def openapi():
        return jsonify(app.config["openapi_spec"]), 200

    @app.post("/api/v1/anomaly/jobs")
    def submit_anomaly_job():
        payload = request.get_json(silent=True) or {}
        entries = payload.get("entries")
        uid = payload.get("uid")

        if not isinstance(entries, list) or not entries:
            return jsonify({"message": "'entries' must be a non-empty array."}), 400

        if any(not _is_valid_entry(item) for item in entries):
            return (
                jsonify(
                    {
                        "message": (
                            "Every entry must include 'log_type', 'raw_line', and "
                            "'message'. Optional 'parsed_fields' must be an object."
                        )
                    }
                ),
                400,
            )

        if uid is not None and (not isinstance(uid, str) or not uid.strip()):
            return jsonify({"message": "'uid' must be a non-empty string when provided."}), 400

        try:
            job_uid = app.config["coordinator"].submit_job(entries=entries, uid=uid)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"message": f"Failed to enqueue job: {exc}"}), 503

        return jsonify({"uid": job_uid, "status": "queued"}), 202

    @app.get("/api/v1/anomaly/jobs/<uid>")
    def fetch_anomaly_job(uid: str):
        result = app.config["coordinator"].get_job(uid)
        if result is None:
            return jsonify({"uid": uid, "status": "pending"}), 200

        return (
            jsonify(
                {
                    "uid": uid,
                    "status": "completed",
                    "started_at": result["started_at"],
                    "ended_at": result["ended_at"],
                    "result": result["result"],
                }
            ),
            200,
        )

    return app
