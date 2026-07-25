from datetime import datetime

from enterprise_os.domain.ceo.context import CEOContext
from enterprise_os.domain.cognition.cycle import CognitiveCycle
from enterprise_os.domain.cognition.decision import DecisionRecord
from enterprise_os.domain.cognition.opportunity import Opportunity
from enterprise_os.domain.cognition.reflection import Reflection
from enterprise_os.domain.cognition.risk import RiskDimension, RiskProfile
from enterprise_os.domain.cognition.strategy import StrategyOption
from enterprise_os.domain.cognition.thought import Thought
from enterprise_os.domain.cognition.types import CONFIDENCE_LEVELS, Confidence


class ExecutiveReasoner:
    def complete_cycle(
        self,
        *,
        context: CEOContext,
        cycle_number: int,
        timestamp: datetime,
    ) -> CognitiveCycle:
        observation = self._observe(context)
        understanding = self._understand(context)
        problems = self._identify_problems(context)
        internal_objectives = self._generate_internal_objectives(context)
        opportunities = self._identify_opportunities(context)
        strategies = self._generate_strategies(context, problems, opportunities)
        risk_profile = self._evaluate_risks(strategies)
        benefits_evaluation = self._evaluate_benefits(strategies)
        challenged_assumptions = self._challenge_assumptions(strategies)
        prioritised_strategies = self._prioritise(strategies)
        decision = self._make_decision(
            problem=problems[0],
            strategies=prioritised_strategies,
            timestamp=timestamp,
        )
        reflection = self._reflect(decision)
        thought = self._structure_thought(
            observation=observation,
            objective=internal_objectives[0],
            opportunities=opportunities,
            strategies=prioritised_strategies,
            risk_profile=risk_profile,
            decision=decision,
        )

        return CognitiveCycle(
            cycle_id=f"cognitive-cycle-{cycle_number}",
            started_at=timestamp,
            observation=observation,
            understanding=understanding,
            problems=problems,
            internal_objectives=internal_objectives,
            opportunities=opportunities,
            strategies=strategies,
            risk_profile=risk_profile,
            benefits_evaluation=benefits_evaluation,
            challenged_assumptions=challenged_assumptions,
            prioritised_strategies=prioritised_strategies,
            decision=decision,
            reflection=reflection,
            thought=thought,
            runtime_learning=(
                "Reasoning remains internal until an approved action boundary exists.",
            ),
        )

    def _observe(self, context: CEOContext) -> str:
        return (
            f"{context.company_state.company_name} is running with "
            f"{len(context.company_state.current_projects)} active initiatives, "
            f"{len(context.company_state.departments)} departments, and "
            f"{len(context.company_state.employees)} employees."
        )

    def _understand(self, context: CEOContext) -> str:
        return (
            "The CEO is permanent, the Founder has superior authority, and all "
            "non-permanent company structure must remain dynamically created later."
        )

    def _identify_problems(self, context: CEOContext) -> tuple[str, ...]:
        if len(context.company_state.current_projects) == 0:
            return ("The company has no active executive initiatives.",)
        return ("The company must keep active initiatives aligned with its mission.",)

    def _generate_internal_objectives(self, context: CEOContext) -> tuple[str, ...]:
        return (
            f"Increase long-term value for {context.company_state.company_name}.",
            "Reduce operational risk before any execution begins.",
            "Discover high-leverage opportunities without external research.",
            "Improve executive reasoning quality.",
        )

    def _identify_opportunities(self, context: CEOContext) -> tuple[Opportunity, ...]:
        return (
            Opportunity(
                title="Clarify executive direction",
                description=(
                    "Convert the current mission into internal strategic focus before "
                    "any operational work exists."
                ),
                expected_value="Improves alignment and reduces premature execution.",
                difficulty="Low",
                uncertainty="Medium",
                assumptions=(
                    "The current mission is sufficient for internal reasoning.",
                    "No external market input is available in this milestone.",
                ),
                recommendation="Proceed as internal reasoning only.",
            ),
            Opportunity(
                title="Protect architectural optionality",
                description=(
                    "Keep reasoning independent from infrastructure so future systems "
                    "can be replaced."
                ),
                expected_value="Preserves clean architecture and future adaptability.",
                difficulty="Medium",
                uncertainty="Low",
                assumptions=(
                    "Future milestones will add persistence and external capabilities.",
                ),
                recommendation="Proceed with strict layer boundaries.",
            ),
        )

    def _generate_strategies(
        self,
        context: CEOContext,
        problems: tuple[str, ...],
        opportunities: tuple[Opportunity, ...],
    ) -> tuple[StrategyOption, ...]:
        return (
            StrategyOption(
                title="Reason conservatively from current state",
                description=(
                    "Use the loaded constitution, owner profile, company state, and "
                    "runtime memory to form internal executive judgment."
                ),
                strengths=("Deterministic", "Aligned with the current milestone"),
                weaknesses=("Limited by absence of external information",),
                risks=("May miss market context",),
                benefits=("Avoids premature execution", "Produces explainable decisions"),
                assumptions=("Current internal state is truthful",),
                confidence="High",
                recommendation="Recommended",
            ),
            StrategyOption(
                title="Wait for more information",
                description="Delay judgment until future external research exists.",
                strengths=("Avoids overconfidence",),
                weaknesses=("Provides no current executive direction",),
                risks=("Creates stagnant runtime behavior",),
                benefits=("Reduces unsupported claims",),
                assumptions=("External research will be available later",),
                confidence="Medium",
                recommendation="Rejected",
                rejection_reason=(
                    "The CEO must complete an internal cognitive cycle now, without "
                    "waiting for future capabilities."
                ),
            ),
            StrategyOption(
                title=f"Focus on {opportunities[0].title.lower()}",
                description=f"Use '{problems[0]}' as the primary reasoning target.",
                strengths=("Directly addresses the observed gap",),
                weaknesses=("Still does not execute work",),
                risks=("Could be mistaken for operational planning if expanded too far",),
                benefits=("Keeps cognition useful while preserving milestone boundaries",),
                assumptions=(context.company_state.current_mission,),
                confidence="High",
                recommendation="Recommended",
            ),
        )

    def _evaluate_risks(self, strategies: tuple[StrategyOption, ...]) -> RiskProfile:
        return RiskProfile(
            dimensions=(
                RiskDimension(
                    name="technical",
                    assessment="Reasoning must stay independent from infrastructure.",
                    mitigation="Keep cognitive structures in the domain layer.",
                    confidence="High",
                ),
                RiskDimension(
                    name="business",
                    assessment="Internal reasoning may lack external validation.",
                    mitigation="Label uncertainty and defer research to a later milestone.",
                    confidence="Medium",
                ),
                RiskDimension(
                    name="financial",
                    assessment="No spending is authorized or performed.",
                    mitigation="Do not cross into action or purchasing.",
                    confidence="High",
                ),
                RiskDimension(
                    name="operational",
                    assessment="The CEO can reason without creating operating structure.",
                    mitigation="Avoid creating departments, employees, or workflows.",
                    confidence="High",
                ),
            ),
            overall_confidence=self._lowest_confidence(
                tuple(strategy.confidence for strategy in strategies)
            ),
        )

    def _prioritise(
        self,
        strategies: tuple[StrategyOption, ...],
    ) -> tuple[StrategyOption, ...]:
        recommended = tuple(
            strategy for strategy in strategies if strategy.recommendation == "Recommended"
        )
        rejected = tuple(
            strategy for strategy in strategies if strategy.recommendation != "Recommended"
        )
        return recommended + rejected

    def _evaluate_benefits(
        self,
        strategies: tuple[StrategyOption, ...],
    ) -> tuple[str, ...]:
        return tuple(
            f"{strategy.title}: {', '.join(strategy.benefits)}"
            for strategy in strategies
        )

    def _challenge_assumptions(
        self,
        strategies: tuple[StrategyOption, ...],
    ) -> tuple[str, ...]:
        return tuple(
            f"{strategy.title}: verify assumption '{assumption}' before execution exists."
            for strategy in strategies
            for assumption in strategy.assumptions
        )

    def _make_decision(
        self,
        *,
        problem: str,
        strategies: tuple[StrategyOption, ...],
        timestamp: datetime,
    ) -> DecisionRecord:
        chosen_strategy = strategies[0]
        return DecisionRecord(
            problem=problem,
            alternatives=strategies,
            reasoning=(
                f"Chosen strategy '{chosen_strategy.title}' is recommended because it "
                "supports explainable executive reasoning without crossing into execution."
            ),
            chosen_strategy=chosen_strategy,
            confidence=chosen_strategy.confidence,
            timestamp=timestamp,
        )

    def _reflect(self, decision: DecisionRecord) -> Reflection:
        return Reflection(
            learned=(
                "The CEO can produce an explainable executive decision from internal "
                "runtime context only."
            ),
            missed_anything=(
                "External evidence is intentionally absent and should be revisited later."
            ),
            should_reconsider=(
                "Reconsider when approved future capabilities provide new evidence."
            ),
            reasoning_improvement=(
                f"Compare rejected alternatives more deeply before acting on "
                f"'{decision.chosen_strategy.title}'."
            ),
        )

    def _structure_thought(
        self,
        *,
        observation: str,
        objective: str,
        opportunities: tuple[Opportunity, ...],
        strategies: tuple[StrategyOption, ...],
        risk_profile: RiskProfile,
        decision: DecisionRecord,
    ) -> Thought:
        return Thought(
            observation=observation,
            objective=objective,
            assumptions=decision.chosen_strategy.assumptions,
            evidence=(
                "Constitution loaded",
                "Owner profile loaded",
                "Company state loaded",
                "Runtime memory loaded",
            ),
            alternatives=tuple(strategy.title for strategy in strategies),
            risks=tuple(dimension.assessment for dimension in risk_profile.dimensions),
            opportunities=tuple(opportunity.title for opportunity in opportunities),
            confidence=decision.confidence,
            recommendation=decision.chosen_strategy.recommendation,
            reasoning=decision.reasoning,
        )

    def _lowest_confidence(self, values: tuple[Confidence, ...]) -> Confidence:
        return min(values, key=CONFIDENCE_LEVELS.index)
