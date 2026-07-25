from enterprise_os.governance.policy_engine import Policy
from enterprise_os.providers.tools.request import ToolRequest

class CommandRestrictionPolicy(Policy):
    def __init__(self):
        self.forbidden_commands = ["rm -rf", "sudo", "mkfs", "chown", "chmod"]

    @property
    def name(self) -> str:
        return "CommandRestriction"

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        if request.tool_name != "SHELL_EXECUTE":
            return True, ""
            
        command = request.arguments.get("command", "")
        if not command:
            return True, ""
            
        for forbidden in self.forbidden_commands:
            if forbidden in command:
                return False, f"Command contains forbidden string '{forbidden}'."
                
        return True, ""
