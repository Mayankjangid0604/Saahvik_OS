from dataclasses import dataclass

from enterprise_os.domain.organisation.blueprint import OrganisationBlueprint
from enterprise_os.domain.organisation.review import OrganisationReview


@dataclass(frozen=True)
class OrganisationalRecommendation:
    executive_summary: str
    blueprint: OrganisationBlueprint
    review: OrganisationReview
    benefits: tuple[str, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    future_concerns: tuple[str, ...]

    def __post_init__(self):
        if not self.blueprint.strategic_goals:
            raise ValueError("OrganisationalRecommendation must trace back to StrategicGoals via the blueprint.")
