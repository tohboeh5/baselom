"""Exception classes for Baselom Core."""


class BaselomError(Exception):
    """Base exception for all Baselom errors."""


class ValidationError(BaselomError):
    """Raised when input validation fails."""


class StateError(BaselomError):
    """Raised when an invalid state transition is attempted."""


class RuleViolationError(BaselomError):
    """Raised when a rule constraint is violated.

    Historically some parts of the code/docs referenced `RuleViolation` (without
    the "Error" suffix). Keep an alias for backwards compatibility.
    """


# Backwards compatible alias for projects that reference ``RuleViolation`` in
# docs or examples (Rust enum uses `RuleViolation`).
RuleViolation = RuleViolationError
