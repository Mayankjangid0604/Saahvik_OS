from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

from enterprise_os.domain.cognition.validation import require_text, require_text_items


@dataclass(frozen=True)
class CompanyState:
    company_name: str
    founder_owner_id: str
    current_mission: str
    founded_on: date
    current_projects: tuple[str, ...]
    departments: tuple[str, ...]
    employees: tuple[str, ...]

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "CompanyState":
        company_name = str(values["company_name"])
        founder_owner_id = str(values["founder_owner_id"])
        current_mission = str(values["current_mission"])
        require_text(company_name, "company_name")
        require_text(founder_owner_id, "founder_owner_id")
        require_text(current_mission, "current_mission")

        return cls(
            company_name=company_name,
            founder_owner_id=founder_owner_id,
            current_mission=current_mission,
            founded_on=date.fromisoformat(str(values["founded_on"])),
            current_projects=require_text_items(
                values["current_projects"],
                "current_projects",
                allow_empty=True,
            ),
            departments=require_text_items(
                values["departments"],
                "departments",
                allow_empty=True,
            ),
            employees=require_text_items(
                values["employees"],
                "employees",
                allow_empty=True,
            ),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "founder_owner_id": self.founder_owner_id,
            "current_mission": self.current_mission,
            "founded_on": self.founded_on.isoformat(),
            "current_projects": list(self.current_projects),
            "departments": list(self.departments),
            "employees": list(self.employees),
        }

    def company_age_days(self, today: date) -> int:
        return (today - self.founded_on).days

    @property
    def has_dynamic_departments(self) -> bool:
        return len(self.departments) == 0

    @property
    def has_dynamic_employees(self) -> bool:
        return len(self.employees) == 0
