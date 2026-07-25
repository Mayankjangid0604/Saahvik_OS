from datetime import datetime, timezone

from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.fact import Fact, FactStatus
from enterprise_os.domain.research.hypothesis import Hypothesis, HypothesisStatus
from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.research.plan import ResearchPlan
from enterprise_os.application.ports.research_provider import ResearchProviderPort


class ResearchOrchestrator:
    def __init__(self, provider: ResearchProviderPort):
        self._provider = provider

    def execute_plan(self, plan: ResearchPlan) -> tuple[Finding, ...]:
        # 1. Gather evidence from provider
        evidence = self._provider.gather_evidence(plan)
        
        if not evidence:
            return ()

        # 2. Extract facts from evidence
        facts = self._build_facts(evidence)
        if not facts:
            return ()

        # 3. Build hypotheses from facts
        hypotheses = self._build_hypotheses(facts)

        # 4. Build findings
        finding = Finding(
            summary=f"Research completed for {len(plan.questions)} questions.",
            hypotheses_used=hypotheses,
            confidence="Medium",
            unresolved_questions=(),
            recommendations=("Proceed with planning",)
        )
        return (finding,)

    def _build_facts(self, evidence: tuple[Evidence, ...]) -> tuple[Fact, ...]:
        return tuple(
            Fact(
                statement=ev.notes,
                supporting_evidence=(ev,),
                confidence=ev.confidence,
                status=FactStatus.VERIFIED
            )
            for ev in evidence
        )

    def _build_hypotheses(self, facts: tuple[Fact, ...]) -> tuple[Hypothesis, ...]:
        return tuple(
            Hypothesis(
                identifier=f"hyp-{i}",
                title=f"Hypothesis derived from {f.statement[:10]}",
                description=f"Generated hypothesis for fact: {f.statement}",
                supporting_facts=(f,),
                assumptions=("Standard conditions apply",),
                confidence=f.confidence,
                status=HypothesisStatus.SUPPORTED,
                reasoning="Directly supported by verified fact.",
                created_timestamp=datetime.now(timezone.utc)
            )
            for i, f in enumerate(facts)
        )
