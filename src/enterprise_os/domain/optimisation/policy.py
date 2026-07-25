from dataclasses import dataclass

@dataclass(frozen=True)
class OptimisationPolicy:
    identifier: str
    name: str
    description: str
    priority: int
