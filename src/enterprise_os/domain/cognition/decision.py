from dataclasses import dataclass
from datetime import datetime
from typing import Any

from enterprise_os.domain.cognition.strategy import StrategyOption
from enterprise_os.domain.cognition.types import Confidence
from enterprise_os.domain.cognition.validation import (
    require_datetime,
    require_confidence,
    require_items,
    require_text,
)


@dataclass(frozen=True)
class DecisionRecord:
    problem: str
    alternatives: tuple[StrategyOption, ...]
    reasoning: str
    chosen_strategy: StrategyOption
    confidence: Confidence
    timestamp: datetime

    def __post_init__(self) -> None:
        require_text(self.problem, "problem")
        require_items(self.alternatives, "alternatives")
        require_text(self.reasoning, "reasoning")
        require_confidence(self.confidence)
        require_datetime(self.timestamp, "timestamp")
        if self.chosen_strategy not in self.alternatives:
            raise ValueError("chosen_strategy must be one of alternatives")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "alternatives": [strategy.to_mapping() for strategy in self.alternatives],
            "reasoning": self.reasoning,
            "chosen_strategy": self.chosen_strategy.to_mapping(),
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }
