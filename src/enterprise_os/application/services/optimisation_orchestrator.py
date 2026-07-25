from enterprise_os.application.services.review_engine import ReviewEngine
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.optimisation.observation import Observation
from enterprise_os.domain.optimisation.proposal import ImprovementProposal
from enterprise_os.domain.optimisation.review import PerformanceReview

class OptimisationOrchestrator:
    def __init__(self, review_engine: ReviewEngine):
        self.review_engine = review_engine

    def evaluate_performance(self, work_items: tuple[WorkItem, ...], observations: tuple[Observation, ...]) -> tuple[ImprovementProposal, ...]:
        review = PerformanceReview(
            scope="General",
            reviewed_work_items=work_items,
            metrics=(),
            observations=observations,
            strengths=(),
            weaknesses=(),
            risks=(),
            opportunities=()
        )
        opportunities = self.review_engine.analyze_knowledge((review,))
        proposals = self.review_engine.generate_proposals(opportunities)
        return proposals
