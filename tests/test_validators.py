"""Tests for validators."""

import pytest

from baselom_core.exceptions import ValidationError
from baselom_core.models import GameState, Score
from baselom_core.validators import validate_state


class TestValidateState:
    """Tests for state validation."""

    def test_valid_state(self, initial_state: GameState) -> None:
        """Test that a valid state passes validation."""
        # Should not raise
        validate_state(initial_state)

    def test_invalid_outs_negative(self) -> None:
        """Test that negative outs fails validation."""
        state = GameState(
            inning=1,
            top=True,
            outs=-1,
            bases=(None, None, None),
            score=Score(),
        )
        with pytest.raises(ValidationError, match="Outs must be between 0 and 2"):
            validate_state(state)

    def test_invalid_outs_too_many(self) -> None:
        """Test that more than 2 outs fails validation."""
        state = GameState(
            inning=1,
            top=True,
            outs=3,
            bases=(None, None, None),
            score=Score(),
        )
        with pytest.raises(ValidationError, match="Outs must be between 0 and 2"):
            validate_state(state)

    def test_invalid_inning_zero(self) -> None:
        """Test that inning 0 fails validation."""
        state = GameState(
            inning=0,
            top=True,
            outs=0,
            bases=(None, None, None),
            score=Score(),
        )
        with pytest.raises(ValidationError, match="Inning must be at least 1"):
            validate_state(state)
