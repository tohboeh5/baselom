"""Exception classes for Baselom Core."""


class BaselomError(Exception):
    """Base exception for all Baselom errors."""


class ValidationError(BaselomError):
    """Raised when input validation fails."""


class StateError(BaselomError):
    """Raised when an invalid state transition is attempted."""


class RuleViolation(BaselomError):
    """Raised when a rule constraint is violated."""
