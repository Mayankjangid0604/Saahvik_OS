from enterprise_os.application.services.evolution_engine import EvolutionEngine
from enterprise_os.domain.evolution.observation import EnterpriseObservation
from enterprise_os.domain.evolution.proposal import ConstitutionAmendmentProposal

class EvolutionOrchestrator:
    def __init__(self, evolution_engine: EvolutionEngine):
        self.evolution_engine = evolution_engine

    def orchestrate_evolution(self, observations: tuple[EnterpriseObservation, ...]) -> tuple[ConstitutionAmendmentProposal, ...]:
        amendments = []
        opportunities = self.evolution_engine.identify_opportunities(observations)
        for opp in opportunities:
            analysis = self.evolution_engine.evaluate_evolution(opp)
            proposal = self.evolution_engine.create_proposal(analysis)
            amendment = self.evolution_engine.draft_amendment(proposal)
            amendments.append(amendment)
        return tuple(amendments)
