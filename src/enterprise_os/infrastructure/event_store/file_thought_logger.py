import json
from pathlib import Path

from enterprise_os.domain.cognition.cycle import CognitiveCycle


class FileThoughtLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_cycle(self, cycle: CognitiveCycle) -> None:
        with self._log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(cycle.to_mapping(), sort_keys=True) + "\n")
