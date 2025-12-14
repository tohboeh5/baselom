"""Baselom Core - Lightweight, pure game-state engine for baseball.

This package provides a high-performance baseball game engine implemented
in Rust with Python bindings via PyO3/maturin.
"""

from baselom_core.engine import apply_pitch, initial_game_state
from baselom_core.exceptions import (
    BaselomError,
    RuleViolation,
    RuleViolationError,
    StateError,
    ValidationError,
)
from baselom_core.models import GameRules, GameState, Score, ValidationResult
from baselom_core.validators import validate_state

__all__ = [
    "BaselomError",
    "GameRules",
    "GameState",
    "RuleViolation",
    "RuleViolationError",
    "Score",
    "StateError",
    "ValidationError",
    "ValidationResult",
    "apply_pitch",
    "initial_game_state",
    "validate_state",
]

__version__ = "0.1.0"
