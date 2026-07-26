from datetime import datetime, timezone
from typing import Any, Mapping

from enterprise_os.domain.cognition.cycle import CognitiveCycle
from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.plan import ResearchPlan
from enterprise_os.application.ports.research_provider import ResearchProviderPort


def valid_documents() -> dict[str, object]:
    return {
        "system.json": {
            "runtime_name": "EnterpriseOS",
            "log_level": "INFO",
            "loop_interval_seconds": 0,
        },
        "owner_profile.json": {
            "owner_id": "owner",
            "display_name": "Owner",
        },
        "company_state.json": {
            "company_name": "EnterpriseOS",
            "founder_owner_id": "owner",
            "current_mission": "Build a Digital CEO operating system.",
            "founded_on": "2026-07-25",
            "current_projects": [],
            "departments": [],
            "employees": [],
        },
        "memory.json": {"entries": [{"kind": "boot_marker"}]},
    }


class InMemoryDocumentStore:
    def __init__(self, documents: Mapping[str, object] | None = None) -> None:
        self.documents = dict(documents or valid_documents())
        self.saved: dict[str, Mapping[str, Any]] = {}

    def load_text(self, name: str) -> str:
        if name == "constitution.md":
            return "# Constitution\n\nThe Owner is above the CEO."
        value = self.documents[name]
        if not isinstance(value, str):
            raise TypeError(f"Expected text document: {name}")
        return value

    def load_mapping(self, name: str) -> Mapping[str, Any]:
        value = self.documents[name]
        if not isinstance(value, dict):
            raise TypeError(f"Expected mapping document: {name}")
        return value

    def save_mapping(self, name: str, values: Mapping[str, Any]) -> None:
        self.saved[name] = dict(values)


class InMemoryActionLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def log_action(
        self,
        action: str,
        *,
        module: str,
        result: str,
        duration_seconds: float,
        error: str | None = None,
        **details: object,
    ) -> None:
        self.events.append(
            {
                "action": action,
                "module": module,
                "result": result,
                "duration_seconds": duration_seconds,
                "error": error,
                "details": details,
            }
        )

    @property
    def actions(self) -> list[str]:
        return [str(event["action"]) for event in self.events]


class InMemoryThoughtLogger:
    def __init__(self) -> None:
        self.cycles: list[CognitiveCycle] = []

    def log_cycle(self, cycle: CognitiveCycle) -> None:
        self.cycles.append(cycle)


class DummyResearchProvider(ResearchProviderPort):
    def gather_evidence(self, plan: ResearchPlan) -> tuple[Evidence, ...]:
        evidence_list = []
        for i, q in enumerate(plan.questions):
            evidence = Evidence(
                identifier=f"ev-dummy-{i}",
                source="DummyProvider",
                source_type="Local",
                retrieval_timestamp=datetime.now(timezone.utc),
                confidence="High",
                reliability="High",
                supporting_facts=("Mock fact for testing.",),
                contradictions=(),
                notes=f"Answer for {q.objective}"
            )
            evidence_list.append(evidence)
        return tuple(evidence_list)
