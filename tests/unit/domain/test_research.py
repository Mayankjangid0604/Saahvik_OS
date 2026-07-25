import pytest
from datetime import datetime, timezone

from enterprise_os.domain.research import (
    Evidence, Fact, FactStatus, Finding, GapStatus, KnowledgeGap,
    ResearchPlan, ResearchQuestion, ExecutiveRecommendation, Source,
    Hypothesis, HypothesisStatus
)

def test_knowledge_gap_is_valid():
    gap = KnowledgeGap(
        identifier="gap-1",
        description="Missing market data",
        reason="Need to evaluate risk",
        priority="High",
        required_evidence=("market_report",),
        status=GapStatus.IDENTIFIED
    )
    assert gap.identifier == "gap-1"

def test_fact_requires_evidence():
    with pytest.raises(ValueError, match="Facts must be derived from evidence"):
        Fact(
            statement="The sky is blue",
            supporting_evidence=(),
            confidence="High",
            status=FactStatus.VERIFIED
        )

def test_hypothesis_requires_facts():
    with pytest.raises(ValueError, match="Hypotheses must be derived from facts"):
        Hypothesis(
            identifier="hyp-1",
            title="Sky color",
            description="Is it blue?",
            supporting_facts=(),
            assumptions=("Daytime",),
            confidence="High",
            status=HypothesisStatus.PROPOSED,
            reasoning="Checking sky color",
            created_timestamp=datetime.now(timezone.utc)
        )

def test_finding_requires_hypothesis():
    with pytest.raises(ValueError, match="Findings must reference one or more hypotheses"):
        Finding(
            summary="Tested finding",
            hypotheses_used=(),
            confidence="High",
            unresolved_questions=(),
            recommendations=()
        )

def test_full_chain_validation():
    ev = Evidence(
        identifier="ev-1",
        source="book",
        source_type="text",
        retrieval_timestamp=datetime.now(timezone.utc),
        confidence="High",
        reliability="High",
        supporting_facts=(),
        contradictions=(),
        notes="Sky is blue"
    )
    fact = Fact(
        statement="The sky is blue",
        supporting_evidence=(ev,),
        confidence="High",
        status=FactStatus.VERIFIED
    )
    hyp = Hypothesis(
        identifier="hyp-1",
        title="Sky color",
        description="Is it blue?",
        supporting_facts=(fact,),
        assumptions=("Daytime",),
        confidence="High",
        status=HypothesisStatus.SUPPORTED,
        reasoning="Fact says so",
        created_timestamp=datetime.now(timezone.utc)
    )
    finding = Finding(
        summary="Tested finding",
        hypotheses_used=(hyp,),
        confidence="High",
        unresolved_questions=(),
        recommendations=()
    )
    rec = ExecutiveRecommendation(summary="Do it", findings=(finding,))
    
    assert rec.findings[0].hypotheses_used[0].supporting_facts[0].supporting_evidence[0] == ev

def test_recommendation_requires_findings():
    with pytest.raises(ValueError, match="Recommendations without evidence"):
        ExecutiveRecommendation(summary="Do it", findings=())
