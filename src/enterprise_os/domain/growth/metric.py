from dataclasses import dataclass

@dataclass(frozen=True)
class GrowthMetric:
    identifier: str
    name: str
    description: str
    value: float
    target: float
    trend: str
    confidence: str
