from dataclasses import dataclass
from enterprise_os.domain.evolution.analysis import EvolutionAnalysis
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class EvolutionProposal:
    identifier: str
    objective: str
    proposed_enterprise_changes: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    risks: tuple[str, ...]
    roadmap: tuple[str, ...]
    confidence: str
    originating_analysis: EvolutionAnalysis

@dataclass(frozen=True)
class ConstitutionAmendmentProposal:
    identifier: str
    affected_principles: tuple[str, ...]
    proposed_amendment: str
    justification: str
    supporting_evidence: tuple[Evidence, ...]
    expected_benefits: tuple[str, ...]
    risks: tuple[str, ...]
    confidence: str
    originating_proposal: EvolutionProposal
