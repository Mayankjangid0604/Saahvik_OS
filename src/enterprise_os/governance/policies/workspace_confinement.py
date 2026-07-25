from pathlib import Path
from enterprise_os.governance.policy_engine import Policy
from enterprise_os.providers.tools.request import ToolRequest

class WorkspaceConfinementPolicy(Policy):
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    @property
    def name(self) -> str:
        return "WorkspaceConfinement"

    def evaluate(self, request: ToolRequest) -> tuple[bool, str]:
        # Only evaluate filesystem requests
        if request.tool_name not in ["FILE_READ", "FILE_WRITE", "FILE_LIST"]:
            return True, ""
            
        path = request.arguments.get("path")
        if not path:
            return True, "" # Leave argument validation to the provider
            
        target_path = (self.workspace_root / path).resolve()
        if not str(target_path).startswith(str(self.workspace_root)):
            return False, f"Access denied: path '{path}' is outside the workspace root."
            
        return True, ""
