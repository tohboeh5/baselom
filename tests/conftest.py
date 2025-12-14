"""Pytest configuration and fixtures."""

import pytest

from baselom_core.models import GameRules, GameState, Score

HOME_LINEUP = tuple(f"h{i}" for i in range(1, 10))
AWAY_LINEUP = tuple(f"a{i}" for i in range(1, 10))


@pytest.fixture
def default_rules() -> GameRules:
    """Provide default game rules."""
    return GameRules()


@pytest.fixture
def valid_lineups() -> dict[str, tuple[str, ...]]:
    """Provide valid home and away lineups."""
    return {"home": HOME_LINEUP, "away": AWAY_LINEUP}


@pytest.fixture
def initial_state(valid_lineups: dict[str, tuple[str, ...]]) -> GameState:
    """Provide an initial game state."""
    return GameState(
        inning=1,
        top=True,
        outs=0,
        bases=(None, None, None),
        score=Score(home=0, away=0),
        lineups=valid_lineups,
    )
