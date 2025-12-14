"""Tests for the data models."""

import pytest

from baselom_core.models import GameRules, GameState, Score


class TestScore:
    """Tests for Score dataclass."""

    def test_default_score(self) -> None:
        """Test default score is 0-0."""
        score = Score()
        assert score.home == 0
        assert score.away == 0

    def test_custom_score(self) -> None:
        """Test creating score with custom values."""
        score = Score(home=3, away=2)
        assert score.home == 3
        assert score.away == 2


class TestGameRules:
    """Tests for GameRules dataclass."""

    def test_default_rules(self) -> None:
        """Test default game rules."""
        rules = GameRules()
        assert rules.designated_hitter is False
        assert rules.max_innings == 9
        assert rules.extra_innings_tiebreaker is None

    def test_custom_rules(self) -> None:
        """Test custom game rules."""
        rules = GameRules(
            designated_hitter=True,
            max_innings=7,
            extra_innings_tiebreaker="runner_on_second",
        )
        assert rules.designated_hitter is True
        assert rules.max_innings == 7
        assert rules.extra_innings_tiebreaker == "runner_on_second"


class TestGameState:
    """Tests for GameState dataclass."""

    def test_initial_state(self, initial_state: GameState) -> None:
        """Test initial game state."""
        assert initial_state.inning == 1
        assert initial_state.top is True
        assert initial_state.outs == 0
        assert initial_state.bases == (None, None, None)
        assert initial_state.score.home == 0
        assert initial_state.score.away == 0

    def test_state_is_immutable(self, initial_state: GameState) -> None:
        """Test that game state is frozen (immutable)."""
        with pytest.raises(AttributeError):
            initial_state.outs = 1  # type: ignore[misc]
