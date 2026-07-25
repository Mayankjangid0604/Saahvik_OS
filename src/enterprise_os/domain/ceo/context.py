from dataclasses import dataclass

from enterprise_os.domain.ceo.company_state import CompanyState
from enterprise_os.domain.ceo.constitution import Constitution
from enterprise_os.domain.ceo.runtime_configuration import RuntimeConfiguration
from enterprise_os.domain.memory.runtime_memory import RuntimeMemory
from enterprise_os.domain.owner.profile import OwnerProfile


@dataclass(frozen=True)
class CEOContext:
    runtime_configuration: RuntimeConfiguration
    constitution: Constitution
    owner_profile: OwnerProfile
    company_state: CompanyState
    memory: RuntimeMemory
