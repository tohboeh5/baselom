"""Pytest configuration and fixtures."""

import pytest

from baselom_core.models import GameRules, GameState, Score


@pytest.fixture
def default_rules() -> GameRules:
    """Provide default game rules."""
    return GameRules()


@pytest.fixture
def initial_state() -> GameState:
    """Provide an initial game state."""
    return GameState(
        inning=1,
        top=True,
        outs=0,
        bases=(None, None, None),
        score=Score(home=0, away=0),
    )
