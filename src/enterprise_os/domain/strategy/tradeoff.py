from dataclasses import dataclass

from enterprise_os.domain.strategy.option import StrategicOption


@dataclass(frozen=True)
class TradeOffDimension:
    name: str
    score: int
    reasoning: str


@dataclass(frozen=True)
class TradeOffProfile:
    option: StrategicOption
    dimensions: tuple[TradeOffDimension, ...]
    overall_score: int
