import time
import urllib.request
import urllib.error
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.provider import ToolProvider
from enterprise_os.providers.tools.capability import ToolCapability

class BrowserProvider(ToolProvider):
    @property
    def name(self) -> str:
        return "browser"

    @property
    def capabilities(self) -> list[ToolCapability]:
        return [ToolCapability.BROWSER_NAVIGATE, ToolCapability.BROWSER_READ]

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        url = request.arguments.get("url")
        
        if not url:
            return ToolResponse(success=False, result="", error_message="Missing 'url'", execution_time=time.time() - start_time)
            
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                if len(content) > 5000:
                    content = content[:5000] + "...(truncated)"
                return ToolResponse(success=True, result=content, execution_time=time.time() - start_time)
        except urllib.error.URLError as e:
            return ToolResponse(success=False, result="", error_message=str(e.reason), execution_time=time.time() - start_time)
        except Exception as e:
            return ToolResponse(success=False, result="", error_message=str(e), execution_time=time.time() - start_time)
