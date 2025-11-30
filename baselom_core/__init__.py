"""Baselom Core - Lightweight, pure game-state engine for baseball.

This package provides a high-performance baseball game engine implemented
in Rust with Python bindings via PyO3/maturin.
"""

from baselom_core.models import GameRules, GameState, Score
from baselom_core.engine import apply_pitch, initial_game_state
from baselom_core.validators import validate_state
from baselom_core.exceptions import BaselomError, StateError, ValidationError

__all__ = [
    "GameRules",
    "GameState",
    "Score",
    "apply_pitch",
    "initial_game_state",
    "validate_state",
    "BaselomError",
    "StateError",
    "ValidationError",
]

__version__ = "0.1.0"
