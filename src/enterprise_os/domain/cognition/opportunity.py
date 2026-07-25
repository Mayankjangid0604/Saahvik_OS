from dataclasses import dataclass
from typing import Any

from enterprise_os.domain.cognition.validation import require_items, require_text


@dataclass(frozen=True)
class Opportunity:
    title: str
    description: str
    expected_value: str
    difficulty: str
    uncertainty: str
    assumptions: tuple[str, ...]
    recommendation: str

    def __post_init__(self) -> None:
        require_text(self.title, "title")
        require_text(self.description, "description")
        require_text(self.expected_value, "expected_value")
        require_text(self.difficulty, "difficulty")
        require_text(self.uncertainty, "uncertainty")
        require_items(self.assumptions, "assumptions")
        require_text(self.recommendation, "recommendation")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "expected_value": self.expected_value,
            "difficulty": self.difficulty,
            "uncertainty": self.uncertainty,
            "assumptions": list(self.assumptions),
            "recommendation": self.recommendation,
        }
