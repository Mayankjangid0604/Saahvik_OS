from datetime import datetime, timezone
from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.plan import ResearchPlan
from enterprise_os.application.ports.research_provider import ResearchProviderPort


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
