import os
import time
from pathlib import Path
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.provider import ToolProvider

from enterprise_os.providers.tools.capability import ToolCapability

class FilesystemProvider(ToolProvider):
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def capabilities(self) -> list[ToolCapability]:
        return [ToolCapability.FILE_READ, ToolCapability.FILE_WRITE, ToolCapability.FILE_LIST]

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        
        try:
            if request.tool_name == "FILE_READ":
                result = self._read_file(request.arguments.get("path", ""))
            elif request.tool_name == "FILE_WRITE":
                result = self._write_file(request.arguments.get("path", ""), request.arguments.get("content", ""))
            elif request.tool_name == "FILE_LIST":
                result = self._list_dir(request.arguments.get("path", ""))
            else:
                raise ValueError(f"Unknown tool {request.tool_name}")
                
            return ToolResponse(
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResponse(
                success=False,
                result="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _resolve_safe_path(self, relative_path: str) -> Path:
        target_path = (self.workspace_root / relative_path).resolve()
        if not str(target_path).startswith(str(self.workspace_root)):
            raise PermissionError("Access denied: path is outside the workspace root.")
        return target_path

    def _read_file(self, path: str) -> str:
        target = self._resolve_safe_path(path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File {path} not found.")
        with open(target, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, path: str, content: str) -> str:
        target = self._resolve_safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    def _list_dir(self, path: str) -> list[str]:
        target = self._resolve_safe_path(path)
        if not target.exists() or not target.is_dir():
            raise NotADirectoryError(f"Directory {path} not found.")
        return [str(p.relative_to(self.workspace_root)) for p in target.iterdir()]
