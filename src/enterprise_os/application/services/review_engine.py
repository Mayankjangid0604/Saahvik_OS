from enterprise_os.domain.optimisation.opportunity import ImprovementOpportunity
from enterprise_os.domain.optimisation.proposal import ImprovementProposal
from enterprise_os.domain.optimisation.review import PerformanceReview

class ReviewEngine:
    def analyze_knowledge(self, reviews: tuple[PerformanceReview, ...]) -> tuple[ImprovementOpportunity, ...]:
        opportunities = []
        for review in reviews:
            opportunities.append(
                ImprovementOpportunity(
                    identifier=f"opp-{review.scope}",
                    title=f"Improvement for {review.scope}",
                    description="Identified an opportunity based on observations.",
                    expected_benefit="High value",
                    implementation_cost="Low",
                    implementation_complexity="Medium",
                    confidence="Medium",
                    supporting_observations=review.observations,
                    supporting_lessons=()
                )
            )
        return tuple(opportunities)

    def generate_proposals(self, opportunities: tuple[ImprovementOpportunity, ...]) -> tuple[ImprovementProposal, ...]:
        proposals = []
        for opp in opportunities:
            proposals.append(
                ImprovementProposal(
                    identifier=f"prop-{opp.identifier}",
                    objective=opp.title,
                    affected_organisation=("Engineering",),
                    affected_strategy=("Strategy A",),
                    expected_impact=opp.expected_benefit,
                    implementation_roadmap=("Step 1", "Step 2"),
                    risks=("Risk 1",),
                    assumptions=("Assumption 1",),
                    confidence=opp.confidence
                )
            )
        return tuple(proposals)
