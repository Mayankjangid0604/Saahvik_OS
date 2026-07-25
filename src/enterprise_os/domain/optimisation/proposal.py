from dataclasses import dataclass

@dataclass(frozen=True)
class ImprovementProposal:
    identifier: str
    objective: str
    affected_organisation: tuple[str, ...]
    affected_strategy: tuple[str, ...]
    expected_impact: str
    implementation_roadmap: tuple[str, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: str
