import json
from typing import Any
from urllib import error, request

from app.decorators import log_gateway_call


class AuthServiceUnavailableError(ConnectionError):
    pass


class AuthServiceHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        cassandra_logger: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._cassandra_logger = cassandra_logger

    def _post_json(self, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        auth_request = request.Request(
            f"{self._base_url}{path}",
            data=body,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(auth_request, timeout=self._timeout_seconds) as response:
                status_code = response.getcode()
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            status_code = exc.code
            response_body = exc.read().decode("utf-8")
        except error.URLError as exc:
            raise AuthServiceUnavailableError(f"Auth service unavailable: {exc.reason}") from exc
        except OSError as exc:
            raise AuthServiceUnavailableError(f"Auth service unavailable: {exc}") from exc

        try:
            payload_data = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError as exc:
            raise AuthServiceUnavailableError("Auth service returned invalid JSON.") from exc

        if not isinstance(payload_data, dict):
            raise AuthServiceUnavailableError("Auth service returned an unexpected payload.")

        return status_code, payload_data

    @log_gateway_call(destination="auth_service", action="auth_login")
    def login(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._post_json("/login", payload)

    @log_gateway_call(destination="auth_service", action="auth_register")
    def register(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._post_json("/register", payload)

    @log_gateway_call(destination="auth_service", action="auth_session_login")
    def session_login(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._post_json("/session-login", payload)
