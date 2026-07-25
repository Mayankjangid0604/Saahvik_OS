from dataclasses import dataclass
from datetime import datetime
from typing import Any

from enterprise_os.domain.cognition.decision import DecisionRecord
from enterprise_os.domain.cognition.opportunity import Opportunity
from enterprise_os.domain.cognition.reflection import Reflection
from enterprise_os.domain.cognition.risk import RiskProfile
from enterprise_os.domain.cognition.strategy import StrategyOption
from enterprise_os.domain.cognition.thought import Thought
from enterprise_os.domain.cognition.validation import (
    require_datetime,
    require_items,
    require_text,
)


@dataclass(frozen=True)
class CognitiveCycle:
    cycle_id: str
    started_at: datetime
    observation: str
    understanding: str
    problems: tuple[str, ...]
    internal_objectives: tuple[str, ...]
    opportunities: tuple[Opportunity, ...]
    strategies: tuple[StrategyOption, ...]
    risk_profile: RiskProfile
    benefits_evaluation: tuple[str, ...]
    challenged_assumptions: tuple[str, ...]
    prioritised_strategies: tuple[StrategyOption, ...]
    decision: DecisionRecord
    reflection: Reflection
    thought: Thought
    runtime_learning: tuple[str, ...]

    def __post_init__(self) -> None:
        require_text(self.cycle_id, "cycle_id")
        require_datetime(self.started_at, "started_at")
        require_text(self.observation, "observation")
        require_text(self.understanding, "understanding")
        require_items(self.problems, "problems")
        require_items(self.internal_objectives, "internal_objectives")
        require_items(self.opportunities, "opportunities")
        require_items(self.strategies, "strategies")
        require_items(self.benefits_evaluation, "benefits_evaluation")
        require_items(self.challenged_assumptions, "challenged_assumptions")
        require_items(self.prioritised_strategies, "prioritised_strategies")
        require_items(self.runtime_learning, "runtime_learning")
        if self.decision.chosen_strategy not in self.prioritised_strategies:
            raise ValueError("decision must choose a prioritised strategy")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at.isoformat(),
            "observation": self.observation,
            "understanding": self.understanding,
            "problems": list(self.problems),
            "internal_objectives": list(self.internal_objectives),
            "opportunities": [opportunity.to_mapping() for opportunity in self.opportunities],
            "strategies": [strategy.to_mapping() for strategy in self.strategies],
            "risk_profile": self.risk_profile.to_mapping(),
            "benefits_evaluation": list(self.benefits_evaluation),
            "challenged_assumptions": list(self.challenged_assumptions),
            "prioritised_strategies": [
                strategy.title for strategy in self.prioritised_strategies
            ],
            "decision": self.decision.to_mapping(),
            "reflection": self.reflection.to_mapping(),
            "thought": self.thought.to_mapping(),
            "runtime_learning": list(self.runtime_learning),
        }
