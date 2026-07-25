class AIPlatformError(Exception):
    """Base class for AI Platform errors."""

class ProviderUnavailableError(AIPlatformError):
    """Raised when a specific provider is down."""

class ModelNotFoundError(AIPlatformError):
    """Raised when a requested model is not found."""

class CapabilityNotSupportedError(AIPlatformError):
    """Raised when no model supports the requested capability."""

class RoutingError(AIPlatformError):
    """Raised when the router cannot find a suitable model for a request."""
