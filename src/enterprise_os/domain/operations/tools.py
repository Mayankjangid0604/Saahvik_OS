from abc import ABC, abstractmethod

class ToolInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

class FilesystemTool(ToolInterface):
    pass

class TerminalTool(ToolInterface):
    pass

class BrowserTool(ToolInterface):
    pass

class GitTool(ToolInterface):
    pass

class PythonTool(ToolInterface):
    pass

class APITool(ToolInterface):
    pass
