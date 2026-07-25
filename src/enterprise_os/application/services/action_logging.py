from time import perf_counter
from typing import Callable, TypeVar

from enterprise_os.application.ports.action_logger import ActionLogger


T = TypeVar("T")


def logged_action(
    action_logger: ActionLogger,
    *,
    action: str,
    module: str,
    operation: Callable[[], T],
) -> T:
    started_at = perf_counter()
    try:
        result = operation()
    except Exception as exc:
        action_logger.log_action(
            action,
            module=module,
            result="failure",
            duration_seconds=perf_counter() - started_at,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise

    action_logger.log_action(
        action,
        module=module,
        result="success",
        duration_seconds=perf_counter() - started_at,
    )
    return result
