from dataclasses import dataclass

@dataclass(frozen=True)
class Metric:
    identifier: str
    name: str
    description: str
    value: float
    target: float
    trend: str
    confidence: str
