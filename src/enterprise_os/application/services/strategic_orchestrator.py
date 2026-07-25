from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.domain.strategy.option import StrategicOption
from enterprise_os.domain.strategy.tradeoff import TradeOffDimension, TradeOffProfile
from enterprise_os.domain.strategy.prioritisation import Prioritisation
from enterprise_os.domain.strategy.decision import ExecutiveDecision
from enterprise_os.domain.strategy.recommendation import FounderRecommendation

class StrategicOrchestrator:
    def execute_cycle(self, goal: StrategicGoal, findings: tuple[Finding, ...]) -> FounderRecommendation:
        options = self._generate_options(goal, findings)
        tradeoffs = self._evaluate_tradeoffs(options)
        prioritised = self._prioritise(tradeoffs, findings)
        decision = self._create_decision(prioritised)
        recommendation = self._create_recommendation(decision, findings)
        return recommendation

    def _generate_options(self, goal: StrategicGoal, findings: tuple[Finding, ...]) -> tuple[StrategicOption, ...]:
        # Generate multiple options as required
        return (
            StrategicOption(
                identifier="opt-1",
                title="Aggressive Expansion",
                description="Expand quickly based on findings.",
                related_goal=goal,
                assumptions=("Market is ready",),
                required_findings=findings,
                expected_benefits=("High growth",),
                expected_costs=("High cost",),
                risks=("High risk",),
                opportunities=("First mover",),
                confidence="Medium"
            ),
            StrategicOption(
                identifier="opt-2",
                title="Conservative Growth",
                description="Grow slowly and steadily.",
                related_goal=goal,
                assumptions=("Market is volatile",),
                required_findings=findings,
                expected_benefits=("Low risk",),
                expected_costs=("Low cost",),
                risks=("Missed opportunities",),
                opportunities=("Stability",),
                confidence="High"
            )
        )

    def _evaluate_tradeoffs(self, options: tuple[StrategicOption, ...]) -> tuple[TradeOffProfile, ...]:
        return tuple(
            TradeOffProfile(
                option=opt,
                dimensions=(
                    TradeOffDimension(name="value", score=8 if "Aggressive" in opt.title else 5, reasoning="Value scale"),
                    TradeOffDimension(name="cost", score=2 if "Aggressive" in opt.title else 8, reasoning="Cost scale")
                ),
                overall_score=10 if "Aggressive" in opt.title else 13
            )
            for opt in options
        )

    def _prioritise(self, tradeoffs: tuple[TradeOffProfile, ...], findings: tuple[Finding, ...]) -> tuple[Prioritisation, ...]:
        # Sort by overall_score descending
        sorted_tradeoffs = sorted(tradeoffs, key=lambda t: t.overall_score, reverse=True)
        return tuple(
            Prioritisation(
                option=t.option,
                relative_priority=i + 1,
                reasoning=f"Scored {t.overall_score}",
                supporting_findings=findings,
                assumptions=t.option.assumptions,
                tradeoff_profile=t
            )
            for i, t in enumerate(sorted_tradeoffs)
        )

    def _create_decision(self, prioritisations: tuple[Prioritisation, ...]) -> ExecutiveDecision:
        selected = prioritisations[0]
        rejected = tuple(p.option for p in prioritisations[1:])
        return ExecutiveDecision(
            selected_option=selected.option,
            rejected_alternatives=rejected,
            reasoning=selected.reasoning,
            confidence=selected.option.confidence,
            expected_impact="Positive long term value",
            supporting_findings=selected.supporting_findings,
            assumptions=selected.assumptions
        )

    def _create_recommendation(self, decision: ExecutiveDecision, findings: tuple[Finding, ...]) -> FounderRecommendation:
        return FounderRecommendation(
            executive_summary=f"Recommend {decision.selected_option.title}",
            decision=decision,
            benefits=decision.selected_option.expected_benefits,
            risks=decision.selected_option.risks,
            assumptions=decision.assumptions,
            confidence=decision.confidence,
            supporting_findings=findings,
            open_questions=()
        )
