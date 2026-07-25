import pytest
from datetime import datetime, timezone

from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.domain.organisation.blueprint import OrganisationBlueprint
from enterprise_os.domain.organisation.review import OrganisationReview
from enterprise_os.domain.organisation.recommendation import OrganisationalRecommendation


def test_organisation_recommendation_requires_goals():
    blueprint = OrganisationBlueprint(
        strategic_goals=(),
        capabilities=(),
        functions=(),
        departments=(),
        roles=(),
        reporting_graph=(),
        rationale="None"
    )
    review = OrganisationReview((), (), (), (), (), (), "None")
    
    with pytest.raises(ValueError, match="OrganisationalRecommendation must trace back to StrategicGoals"):
        OrganisationalRecommendation(
            executive_summary="sum",
            blueprint=blueprint,
            review=review,
            benefits=(),
            risks=(),
            assumptions=(),
            future_concerns=()
        )
