class DepDetectError(Exception):
    """Base exception for scanner and integration errors."""


class InvalidRootError(DepDetectError):
    """Raised when the scan target is not a valid directory."""


class LinguistUnavailableError(DepDetectError):
    """Raised when github-linguist is not available in PATH."""


class LinguistExecutionError(DepDetectError):
    """Raised when github-linguist exits unsuccessfully."""


class LinguistOutputError(DepDetectError):
    """Raised when github-linguist output cannot be parsed."""
