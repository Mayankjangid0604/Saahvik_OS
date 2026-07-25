import subprocess
import time
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.provider import ToolProvider

from enterprise_os.providers.tools.capability import ToolCapability

class ShellProvider(ToolProvider):
    @property
    def name(self) -> str:
        return "shell"

    @property
    def capabilities(self) -> list[ToolCapability]:
        return [ToolCapability.SHELL_EXECUTE]

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        command = request.arguments.get("command")
        timeout = request.arguments.get("timeout", 30)
        
        if not command:
            return ToolResponse(
                success=False,
                result="",
                error_message="Missing 'command' argument.",
                execution_time=time.time() - start_time
            )
            
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = process.stdout if process.returncode == 0 else process.stderr
            return ToolResponse(
                success=process.returncode == 0,
                result=output.strip(),
                error_message=output.strip() if process.returncode != 0 else "",
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return ToolResponse(
                success=False,
                result="",
                error_message=f"Command timed out after {timeout} seconds.",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                result="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
