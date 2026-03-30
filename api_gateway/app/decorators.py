from functools import wraps
from typing import Any, Callable


def log_gateway_call(
    *,
    destination: str,
    action: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self, *args, **kwargs):  # noqa: ANN001
            logger = getattr(self, "_cassandra_logger", None)
            if logger is not None:
                logger.safe_write_log(
                    source="api_gateway",
                    destination=destination,
                    action=f"{action}:request",
                )

            try:
                result = func(self, *args, **kwargs)
                if logger is not None:
                    logger.safe_write_log(
                        source=destination,
                        destination="api_gateway",
                        action=f"{action}:response",
                    )
                return result
            except Exception as exc:
                if logger is not None:
                    logger.safe_write_log(
                        source=destination,
                        destination="api_gateway",
                        action=f"{action}:error:{type(exc).__name__}",
                    )
                raise exc

        return wrapper

    return decorator
