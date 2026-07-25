from dataclasses import dataclass

@dataclass(frozen=True)
class GovernancePolicy:
    identifier: str
    name: str
    description: str
    parameters: dict[str, str]
