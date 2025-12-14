"""Tests for validators."""

from baselom_core.models import GameState, Score
from baselom_core.validators import validate_state


class TestValidateState:
    """Tests for state validation."""

    def test_valid_state(self, initial_state: GameState) -> None:
        """Test that a valid state passes validation."""
        result = validate_state(initial_state)
        assert result.is_valid is True
        assert result.errors == ()
        assert result.warnings == ()

    def test_invalid_outs_negative(self, valid_lineups: dict[str, tuple[str, ...]]) -> None:
        """Test that negative outs fails validation."""
        state = GameState(
            inning=1,
            top=True,
            outs=-1,
            bases=(None, None, None),
            score=Score(),
            lineups=valid_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "outs must be in range [0, 2], got -1" in result.errors

    def test_invalid_outs_too_many(self, valid_lineups: dict[str, tuple[str, ...]]) -> None:
        """Test that more than 2 outs fails validation."""
        state = GameState(
            inning=1,
            top=True,
            outs=3,
            bases=(None, None, None),
            score=Score(),
            lineups=valid_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "outs must be in range [0, 2], got 3" in result.errors

    def test_invalid_inning_zero(self, valid_lineups: dict[str, tuple[str, ...]]) -> None:
        """Test that inning 0 fails validation."""
        state = GameState(
            inning=0,
            top=True,
            outs=0,
            bases=(None, None, None),
            score=Score(),
            lineups=valid_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "inning must be >= 1, got 0" in result.errors

    def test_negative_scores_invalid(self, valid_lineups: dict[str, tuple[str, ...]]) -> None:
        """Scores must be non-negative."""
        state = GameState(
            inning=1,
            top=True,
            outs=0,
            bases=(None, None, None),
            score=Score(home=-1, away=0),
            lineups=valid_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "scores must be non-negative" in result.errors[0]

    def test_lineup_size_must_be_nine(
        self, valid_lineups: dict[str, tuple[str, ...]],
    ) -> None:
        """Lineups must contain exactly 9 players."""
        bad_lineups = dict(valid_lineups)
        bad_lineups["home"] = bad_lineups["home"][:8]
        state = GameState(
            inning=1,
            top=True,
            outs=0,
            bases=(None, None, None),
            score=Score(),
            lineups=bad_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "lineup must contain exactly 9 players, got 8 for home" in result.errors

    def test_lineup_duplicates_detected(
        self, valid_lineups: dict[str, tuple[str, ...]],
    ) -> None:
        """Duplicate players in lineup are invalid."""
        bad_lineups = dict(valid_lineups)
        bad_lineups["away"] = (
            "a1",
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "a6",
            "a7",
            "a8",
        )
        state = GameState(
            inning=1,
            top=True,
            outs=0,
            bases=(None, None, None),
            score=Score(),
            lineups=bad_lineups,
        )
        result = validate_state(state)
        assert result.is_valid is False
        assert "duplicate player 'a1' in away lineup" in result.errors
