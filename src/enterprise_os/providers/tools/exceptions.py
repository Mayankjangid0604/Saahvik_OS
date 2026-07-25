class ToolPlatformError(Exception):
    """Base class for Tool Platform errors."""

class ToolNotFoundError(ToolPlatformError):
    """Raised when a requested tool cannot be routed to any provider."""

class ToolExecutionError(ToolPlatformError):
    """Raised when a tool execution fails at the provider level."""
