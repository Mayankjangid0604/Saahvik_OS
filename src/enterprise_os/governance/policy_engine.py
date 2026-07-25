from typing import Protocol, Any
from enterprise_os.providers.tools.request import ToolRequest

class Policy(Protocol):
    @property
    def name(self) -> str:
        ...

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        """
        Evaluates a tool request against this policy.
        Returns (True, "") if approved, (False, "Reason") if rejected.
        """
        ...

class PolicyEngine:
    def __init__(self) -> None:
        self._policies: list[Policy] = []

    def register_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        for policy in self._policies:
            approved, reason = policy.evaluate(request)
            if not approved:
                return False, f"Policy Violation ({policy.name}): {reason}"
        return True, ""
