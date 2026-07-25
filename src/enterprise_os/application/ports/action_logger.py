from typing import Protocol


class ActionLogger(Protocol):
    def log_action(
        self,
        action: str,
        *,
        module: str,
        result: str,
        duration_seconds: float,
        error: str | None = None,
        **details: object,
    ) -> None:
        ...
