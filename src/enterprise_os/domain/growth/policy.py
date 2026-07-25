from dataclasses import dataclass

@dataclass(frozen=True)
class GrowthPolicy:
    identifier: str
    name: str
    description: str
    priority: int
