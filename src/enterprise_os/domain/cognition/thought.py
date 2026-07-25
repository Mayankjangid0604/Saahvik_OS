from dataclasses import dataclass
from typing import Any

from enterprise_os.domain.cognition.types import Confidence
from enterprise_os.domain.cognition.validation import (
    require_confidence,
    require_items,
    require_text,
)


@dataclass(frozen=True)
class Thought:
    observation: str
    objective: str
    assumptions: tuple[str, ...]
    evidence: tuple[str, ...]
    alternatives: tuple[str, ...]
    risks: tuple[str, ...]
    opportunities: tuple[str, ...]
    confidence: Confidence
    recommendation: str
    reasoning: str

    def __post_init__(self) -> None:
        require_text(self.observation, "observation")
        require_text(self.objective, "objective")
        require_items(self.assumptions, "assumptions")
        require_items(self.evidence, "evidence")
        require_items(self.alternatives, "alternatives")
        require_items(self.risks, "risks")
        require_items(self.opportunities, "opportunities")
        require_confidence(self.confidence)
        require_text(self.recommendation, "recommendation")
        require_text(self.reasoning, "reasoning")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "observation": self.observation,
            "objective": self.objective,
            "assumptions": list(self.assumptions),
            "evidence": list(self.evidence),
            "alternatives": list(self.alternatives),
            "risks": list(self.risks),
            "opportunities": list(self.opportunities),
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
        }
