from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter

from enterprise_os.application.ports.action_logger import ActionLogger
from enterprise_os.application.ports.thought_logger import ThoughtLogger
from enterprise_os.domain.ceo.context import CEOContext
from enterprise_os.domain.cognition.cycle import CognitiveCycle
from enterprise_os.domain.cognition.reasoning import ExecutiveReasoner


MODULE_NAME = "application.cognitive_engine"


class CognitiveEngine:
    def __init__(
        self,
        *,
        context: CEOContext,
        reasoner: ExecutiveReasoner,
        thought_logger: ThoughtLogger,
        action_logger: ActionLogger,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._context = context
        self._reasoner = reasoner
        self._thought_logger = thought_logger
        self._action_logger = action_logger
        self._clock = clock or (lambda: datetime.now(UTC))
        self._cycles_completed = 0

    def complete_cycle(self) -> CognitiveCycle:
        cycle_number = self._cycles_completed + 1
        started_at = perf_counter()
        self._action_logger.log_action(
            "cognitive_cycle_started",
            module=MODULE_NAME,
            result="started",
            duration_seconds=0.0,
            cycle=cycle_number,
        )

        try:
            cycle = self._reasoner.complete_cycle(
                context=self._context,
                cycle_number=cycle_number,
                timestamp=self._clock(),
            )
            self._thought_logger.log_cycle(cycle)
        except Exception as exc:
            self._action_logger.log_action(
                "cognitive_cycle_failed",
                module=MODULE_NAME,
                result="failure",
                duration_seconds=perf_counter() - started_at,
                error=f"{type(exc).__name__}: {exc}",
                cycle=cycle_number,
            )
            raise

        self._cycles_completed = cycle_number
        self._action_logger.log_action(
            "cognitive_cycle_completed",
            module=MODULE_NAME,
            result="success",
            duration_seconds=perf_counter() - started_at,
            cycle=cycle_number,
            decision=cycle.decision.chosen_strategy.title,
        )
        return cycle

    @property
    def cycles_completed(self) -> int:
        return self._cycles_completed
