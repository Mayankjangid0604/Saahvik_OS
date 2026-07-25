from dataclasses import dataclass
from enterprise_os.domain.organisation.capability import Capability

@dataclass(frozen=True)
class Responsibility:
    identifier: str
    title: str
    description: str
    expected_outcome: str
    required_capabilities: tuple[Capability, ...]
    success_criteria: tuple[str, ...]
    authority_level: str
    dependencies: tuple[str, ...]
