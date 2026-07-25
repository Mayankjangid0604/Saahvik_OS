from dataclasses import dataclass
from typing import Any

from enterprise_os.domain.cognition.types import Confidence, StrategyRecommendation
from enterprise_os.domain.cognition.validation import (
    require_confidence,
    require_items,
    require_text,
)


@dataclass(frozen=True)
class StrategyOption:
    title: str
    description: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    risks: tuple[str, ...]
    benefits: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: Confidence
    recommendation: StrategyRecommendation
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        require_text(self.title, "title")
        require_text(self.description, "description")
        require_items(self.strengths, "strengths")
        require_items(self.weaknesses, "weaknesses")
        require_items(self.risks, "risks")
        require_items(self.benefits, "benefits")
        require_items(self.assumptions, "assumptions")
        require_confidence(self.confidence)
        if self.recommendation not in ("Recommended", "Rejected"):
            raise ValueError("recommendation must be Recommended or Rejected")
        if self.recommendation == "Rejected":
            if self.rejection_reason is None:
                raise ValueError("rejected strategies must explain rejection_reason")
            require_text(self.rejection_reason, "rejection_reason")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "risks": list(self.risks),
            "benefits": list(self.benefits),
            "assumptions": list(self.assumptions),
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "rejection_reason": self.rejection_reason,
        }
