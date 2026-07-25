import subprocess
import time
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.provider import ToolProvider

from enterprise_os.providers.tools.capability import ToolCapability

class PythonProvider(ToolProvider):
    @property
    def name(self) -> str:
        return "python"

    @property
    def capabilities(self) -> list[ToolCapability]:
        return [ToolCapability.PYTHON_EXECUTE]

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        script = request.arguments.get("script")
        
        if not script:
            return ToolResponse(success=False, result="", error_message="Missing 'script' argument", execution_time=time.time() - start_time)
            
        try:
            process = subprocess.run(
                ["python", "-c", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            return ToolResponse(
                success=process.returncode == 0,
                result=process.stdout.strip(),
                error_message=process.stderr.strip() if process.returncode != 0 else "",
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return ToolResponse(success=False, result="", error_message="Python script timed out", execution_time=time.time() - start_time)
        except Exception as e:
            return ToolResponse(success=False, result="", error_message=str(e), execution_time=time.time() - start_time)
