from dataclasses import dataclass

@dataclass(frozen=True)
class ConfidenceLevel:
    score: float # 0.0 to 1.0
    rationale: str
    
    @property
    def is_sufficient(self) -> bool:
        return self.score >= 0.8
