from dataclasses import dataclass
from typing import Any

from enterprise_os.domain.cognition.validation import require_text


@dataclass(frozen=True)
class Reflection:
    learned: str
    missed_anything: str
    should_reconsider: str
    reasoning_improvement: str

    def __post_init__(self) -> None:
        require_text(self.learned, "learned")
        require_text(self.missed_anything, "missed_anything")
        require_text(self.should_reconsider, "should_reconsider")
        require_text(self.reasoning_improvement, "reasoning_improvement")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "learned": self.learned,
            "missed_anything": self.missed_anything,
            "should_reconsider": self.should_reconsider,
            "reasoning_improvement": self.reasoning_improvement,
        }
