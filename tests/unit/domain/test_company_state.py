from datetime import date

from enterprise_os.domain.ceo.company_state import CompanyState


def test_company_state_knows_required_milestone_fields() -> None:
    company_state = CompanyState.from_mapping(
        {
            "company_name": "EnterpriseOS",
            "founder_owner_id": "owner",
            "current_mission": "Build a Digital CEO operating system.",
            "founded_on": "2026-07-25",
            "current_projects": [],
            "departments": [],
            "employees": [],
        }
    )

    assert company_state.company_name == "EnterpriseOS"
    assert company_state.founder_owner_id == "owner"
    assert company_state.current_mission == "Build a Digital CEO operating system."
    assert company_state.company_age_days(date(2026, 7, 26)) == 1
    assert company_state.current_projects == ()
    assert company_state.departments == ()
    assert company_state.employees == ()
    assert company_state.has_dynamic_departments
    assert company_state.has_dynamic_employees


def test_company_state_rejects_blank_or_malformed_values() -> None:
    try:
        CompanyState.from_mapping(
            {
                "company_name": "",
                "founder_owner_id": "owner",
                "current_mission": "Build a Digital CEO operating system.",
                "founded_on": "2026-07-25",
                "current_projects": "not-a-list",
                "departments": [],
                "employees": [],
            }
        )
    except (TypeError, ValueError) as exc:
        message = str(exc)
        assert "company_name" in message or "current_projects" in message
    else:
        raise AssertionError("CompanyState should reject malformed core fields")
