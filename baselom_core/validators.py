"""State validation rules."""

from baselom_core.exceptions import ValidationError
from baselom_core.models import GameState


def validate_state(state: GameState) -> None:
    """Validate that a game state is consistent.

    Args:
        state: The game state to validate.

    Raises:
        ValidationError: If the state is invalid.
    """
    # Validate outs
    if not 0 <= state.outs <= 2:
        raise ValidationError("Outs must be between 0 and 2")

    # Validate inning
    if state.inning < 1:
        raise ValidationError("Inning must be at least 1")
