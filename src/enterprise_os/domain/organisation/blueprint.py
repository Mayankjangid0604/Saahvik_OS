from dataclasses import dataclass

from enterprise_os.domain.organisation.capability import Capability
from enterprise_os.domain.organisation.function import BusinessFunction
from enterprise_os.domain.strategy.goal import StrategicGoal


@dataclass(frozen=True)
class DepartmentBlueprint:
    identifier: str
    purpose: str
    supported_capabilities: tuple[Capability, ...]
    supported_functions: tuple[BusinessFunction, ...]
    responsibilities: tuple[str, ...]
    interfaces: tuple[str, ...]
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class RoleBlueprint:
    identifier: str
    title: str
    purpose: str
    required_capabilities: tuple[Capability, ...]
    responsibilities: tuple[str, ...]
    authority: str
    reporting_relationships: tuple[str, ...]


@dataclass(frozen=True)
class OrganisationBlueprint:
    strategic_goals: tuple[StrategicGoal, ...]
    capabilities: tuple[Capability, ...]
    functions: tuple[BusinessFunction, ...]
    departments: tuple[DepartmentBlueprint, ...]
    roles: tuple[RoleBlueprint, ...]
    reporting_graph: tuple[str, ...]
    rationale: str
