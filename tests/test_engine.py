"""Tests for pitch/count engine logic."""

from dataclasses import replace

from baselom_core.engine import apply_pitch
from baselom_core.models import GameState


def test_ball_increments_count(initial_state: GameState, default_rules) -> None:
    """A ball should increment ball count without affecting strikes."""
    new_state, event = apply_pitch(initial_state, "ball", default_rules)

    assert new_state.balls == 1
    assert new_state.strikes == 0
    assert event["event_type"] == "ball"


def test_strikeout_resets_count_and_adds_out(initial_state: GameState, default_rules) -> None:
    """Third strike should record an out and reset the count."""
    prepared = replace(initial_state, strikes=2)
    new_state, event = apply_pitch(prepared, "strike_swinging", default_rules)

    assert new_state.outs == initial_state.outs + 1
    assert new_state.balls == 0
    assert new_state.strikes == 0
    assert event["event_type"] == "strikeout_swinging"


def test_walk_places_batter_on_first(initial_state: GameState, default_rules) -> None:
    """Fourth ball should walk the batter to first."""
    prepared = replace(initial_state, balls=3)
    new_state, event = apply_pitch(prepared, "ball", default_rules)

    assert new_state.bases[0] == initial_state.current_batter_id
    assert new_state.balls == 0
    assert new_state.strikes == 0
    assert event["event_type"] == "walk"


def test_third_out_flips_half_inning(initial_state: GameState, default_rules) -> None:
    """Third out should reset outs and flip half-inning."""
    prepared = replace(initial_state, outs=2, strikes=2)
    new_state, _ = apply_pitch(prepared, "strike_called", default_rules)

    assert new_state.outs == 0
    assert new_state.top is False
