import json
from datetime import UTC, datetime
from pathlib import Path


class FileActionLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

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
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "module": module,
            "result": result,
            "duration_seconds": duration_seconds,
            "error": error,
            "details": details,
        }
        with self._log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, sort_keys=True) + "\n")
