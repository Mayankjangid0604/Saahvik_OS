from enterprise_os.application.services.growth_engine import GrowthEngine
from enterprise_os.domain.growth.opportunity import GrowthOpportunity
from enterprise_os.domain.growth.recommendation import InvestmentRecommendation

class GrowthOrchestrator:
    def __init__(self, growth_engine: GrowthEngine):
        self.growth_engine = growth_engine

    def orchestrate_growth(self, opportunities: tuple[GrowthOpportunity, ...]) -> tuple[InvestmentRecommendation, ...]:
        recommendations = []
        for opp in opportunities:
            analysis = self.growth_engine.evaluate_expansion(opp)
            initiatives = self.growth_engine.build_initiatives((analysis,))
            portfolio = self.growth_engine.construct_portfolio(initiatives)
            rec = self.growth_engine.generate_investment_recommendation(portfolio)
            recommendations.append(rec)
        return tuple(recommendations)
