from dataclasses import dataclass
from typing import Any, Mapping

from enterprise_os.domain.cognition.validation import (
    require_non_negative_float,
    require_text,
)


@dataclass(frozen=True)
class RuntimeConfiguration:
    runtime_name: str
    log_level: str
    loop_interval_seconds: float

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "RuntimeConfiguration":
        runtime_name = str(values["runtime_name"])
        log_level = str(values["log_level"])
        require_text(runtime_name, "runtime_name")
        require_text(log_level, "log_level")

        return cls(
            runtime_name=runtime_name,
            log_level=log_level,
            loop_interval_seconds=require_non_negative_float(
                values["loop_interval_seconds"],
                "loop_interval_seconds",
            ),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "runtime_name": self.runtime_name,
            "log_level": self.log_level,
            "loop_interval_seconds": self.loop_interval_seconds,
        }
