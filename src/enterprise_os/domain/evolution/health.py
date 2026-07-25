from dataclasses import dataclass

@dataclass(frozen=True)
class EnterpriseHealth:
    strategic_alignment: str
    organisational_health: str
    operational_maturity: str
    knowledge_maturity: str
    governance_maturity: str
    adaptability: str
