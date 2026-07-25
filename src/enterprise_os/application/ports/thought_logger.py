from typing import Protocol

from enterprise_os.domain.cognition.cycle import CognitiveCycle


class ThoughtLogger(Protocol):
    def log_cycle(self, cycle: CognitiveCycle) -> None:
        ...
