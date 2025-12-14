"""State validation rules."""

from baselom_core.exceptions import ValidationError
from baselom_core.models import GameState

MAX_OUTS = 2
MIN_INNING = 1
OUTS_RANGE_MESSAGE = "Outs must be between 0 and 2"
MIN_INNING_MESSAGE = "Inning must be at least 1"


def validate_state(state: GameState) -> None:
    """Validate that a game state is consistent.

    Args:
        state: The game state to validate.

    Raises:
        ValidationError: If the state is invalid.
    """
    # Validate outs
    if not 0 <= state.outs <= MAX_OUTS:
        raise ValidationError(OUTS_RANGE_MESSAGE)

    # Validate inning
    if state.inning < MIN_INNING:
        raise ValidationError(MIN_INNING_MESSAGE)
