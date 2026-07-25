from dataclasses import dataclass
from typing import Any

from enterprise_os.domain.cognition.types import Confidence
from enterprise_os.domain.cognition.validation import (
    require_confidence,
    require_items,
    require_text,
)


@dataclass(frozen=True)
class RiskDimension:
    name: str
    assessment: str
    mitigation: str
    confidence: Confidence

    def __post_init__(self) -> None:
        require_text(self.name, "name")
        require_text(self.assessment, "assessment")
        require_text(self.mitigation, "mitigation")
        require_confidence(self.confidence)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "assessment": self.assessment,
            "mitigation": self.mitigation,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class RiskProfile:
    dimensions: tuple[RiskDimension, ...]
    overall_confidence: Confidence

    def __post_init__(self) -> None:
        require_items(self.dimensions, "dimensions")
        require_confidence(self.overall_confidence, "overall_confidence")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "dimensions": [dimension.to_mapping() for dimension in self.dimensions],
            "overall_confidence": self.overall_confidence,
        }
