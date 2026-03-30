import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement


class CassandraLogRepository:
    def __init__(
        self,
        *,
        contact_points: list[str],
        port: int,
        keyspace: str,
        table: str,
    ) -> None:
        self._contact_points = contact_points
        self._port = port
        self._keyspace = keyspace
        self._table = table
        self._cluster: Cluster | None = None
        self._session = None

    def _connect(self) -> None:
        if self._session is not None:
            return

        last_error: Exception | None = None
        for _ in range(20):
            try:
                self._cluster = Cluster(contact_points=self._contact_points, port=self._port)
                self._session = self._cluster.connect()
                self._ensure_schema()
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.5)

        raise RuntimeError("Unable to connect to Cassandra cluster.") from last_error

    def _ensure_schema(self) -> None:
        if self._session is None:
            raise RuntimeError("Cassandra session not initialized.")

        create_keyspace_query = f"""
        CREATE KEYSPACE IF NOT EXISTS {self._keyspace}
        WITH REPLICATION = {{
            'class': 'SimpleStrategy',
            'replication_factor': 2
        }}
        """
        self._session.execute(
            SimpleStatement(create_keyspace_query, consistency_level=ConsistencyLevel.QUORUM)
        )
        self._session.set_keyspace(self._keyspace)

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self._table} (
            id UUID PRIMARY KEY,
            source TEXT,
            destination TEXT,
            action TEXT,
            timestamp TIMESTAMP
        )
        """
        self._session.execute(
            SimpleStatement(create_table_query, consistency_level=ConsistencyLevel.QUORUM)
        )

    def write_log(self, *, source: str, destination: str, action: str) -> None:
        self._connect()
        if self._session is None:
            raise RuntimeError("Cassandra session not initialized.")

        insert_query = (
            f"INSERT INTO {self._table} (id, source, destination, action, timestamp) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        statement = SimpleStatement(insert_query, consistency_level=ConsistencyLevel.QUORUM)
        self._session.execute(
            statement,
            (
                uuid4(),
                source,
                destination,
                action,
                datetime.now(UTC),
            ),
        )

    def safe_write_log(self, *, source: str, destination: str, action: str) -> None:
        try:
            self.write_log(source=source, destination=destination, action=action)
        except Exception as exc:  # noqa: BLE001
            print(f"[gateway] cassandra write failed: {exc}")

    def read_logs(self) -> list[dict[str, Any]]:
        self._connect()
        if self._session is None:
            raise RuntimeError("Cassandra session not initialized.")

        query = (
            f"SELECT id, source, destination, action, timestamp "
            f"FROM {self._table}"
        )
        statement = SimpleStatement(query, consistency_level=ConsistencyLevel.QUORUM)
        rows = self._session.execute(statement)

        results: list[dict[str, Any]] = []
        for row in rows:
            timestamp = row.timestamp
            if hasattr(timestamp, "isoformat"):
                timestamp_value = timestamp.isoformat()
            else:
                timestamp_value = str(timestamp)

            results.append(
                {
                    "id": str(row.id),
                    "source": row.source,
                    "destination": row.destination,
                    "action": row.action,
                    "timestamp": timestamp_value,
                }
            )

        results.sort(key=lambda item: item["timestamp"])
        return results

    def close(self) -> None:
        if self._cluster is not None:
            self._cluster.shutdown()
            self._cluster = None
            self._session = None
