from dataclasses import dataclass
from enterprise_os.domain.growth.initiative import StrategicInitiative

@dataclass(frozen=True)
class InitiativePortfolio:
    initiatives: tuple[StrategicInitiative, ...]
    priorities: tuple[str, ...]
    resource_demand: str
    expected_value: str
    overall_risk: str
    alignment: str
