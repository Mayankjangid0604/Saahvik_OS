from collections.abc import Callable
from time import perf_counter, sleep

from enterprise_os.application.ports.action_logger import ActionLogger
from enterprise_os.domain.ceo.context import CEOContext


MODULE_NAME = "application.ceo_runtime"


class CEORuntime:
    def __init__(
        self,
        context: CEOContext,
        action_logger: ActionLogger,
        loop_step: Callable[[], None] | None = None,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self._context = context
        self._action_logger = action_logger
        self._loop_step = loop_step or self._heartbeat
        self._sleeper = sleeper

    def run_forever(self) -> None:
        self.run(max_cycles=None)

    def run(self, max_cycles: int | None) -> None:
        self._action_logger.log_action(
            "ceo_loop_started",
            module=MODULE_NAME,
            result="started",
            duration_seconds=0.0,
        )
        cycles_completed = 0

        while max_cycles is None or cycles_completed < max_cycles:
            cycle = cycles_completed + 1
            self._action_logger.log_action(
                "ceo_loop_cycle_started",
                module=MODULE_NAME,
                result="started",
                duration_seconds=0.0,
                cycle=cycle,
            )

            started_at = perf_counter()
            try:
                self._loop_step()
                self._sleeper(self._loop_interval_seconds())
            except Exception as exc:
                self._action_logger.log_action(
                    "ceo_loop_cycle_recovered",
                    module=MODULE_NAME,
                    result="recovered",
                    duration_seconds=perf_counter() - started_at,
                    error=f"{type(exc).__name__}: {exc}",
                    cycle=cycle,
                )
            else:
                self._action_logger.log_action(
                    "ceo_loop_cycle_completed",
                    module=MODULE_NAME,
                    result="success",
                    duration_seconds=perf_counter() - started_at,
                    cycle=cycle,
                )

            cycles_completed += 1

    @property
    def context(self) -> CEOContext:
        return self._context

    def _loop_interval_seconds(self) -> float:
        return self._context.runtime_configuration.loop_interval_seconds

    def _heartbeat(self) -> None:
        self._action_logger.log_action(
            "ceo_heartbeat",
            module=MODULE_NAME,
            result="success",
            duration_seconds=0.0,
            company_name=self._context.company_state.company_name,
            founder_owner_id=self._context.company_state.founder_owner_id,
        )
