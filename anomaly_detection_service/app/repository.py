import json
from datetime import datetime
from typing import Any

import mysql.connector


class DetectionRepository:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ) -> None:
        self._connection_args = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
        }

    def _connect(self):
        return mysql.connector.connect(**self._connection_args)

    def ping(self) -> bool:
        connection = self._connect()
        try:
            return connection.is_connected()
        finally:
            connection.close()

    def save_detection(
        self,
        *,
        uid: str,
        started_at: datetime,
        ended_at: datetime,
        result: dict[str, Any],
    ) -> None:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO anomaly_detection_runs (uid, started_at, ended_at, detection_result)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  started_at = VALUES(started_at),
                  ended_at = VALUES(ended_at),
                  detection_result = VALUES(detection_result)
                """,
                (
                    uid,
                    started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    ended_at.strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def get_detection(self, uid: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT uid, started_at, ended_at, detection_result
                FROM anomaly_detection_runs
                WHERE uid = %s
                LIMIT 1
                """,
                (uid,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            try:
                parsed_result = json.loads(row["detection_result"])
            except json.JSONDecodeError:
                parsed_result = {"raw": row["detection_result"]}

            return {
                "uid": row["uid"],
                "started_at": row["started_at"].isoformat(),
                "ended_at": row["ended_at"].isoformat(),
                "result": parsed_result,
            }
        finally:
            connection.close()
