from enum import Enum, auto

class ToolCapability(Enum):
    FILE_READ = auto()
    FILE_WRITE = auto()
    FILE_LIST = auto()
    SHELL_EXECUTE = auto()
    PYTHON_EXECUTE = auto()
    GIT_EXECUTE = auto()
    BROWSER_NAVIGATE = auto()
    BROWSER_CLICK = auto()
    BROWSER_READ = auto()
    
    @classmethod
    def from_string(cls, value: str) -> "ToolCapability":
        try:
            return cls[value.upper()]
        except KeyError as e:
            raise ValueError(f"Unknown capability: {value}") from e
