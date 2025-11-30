"""JSON serialization/deserialization for Baselom models."""

import json
from typing import Any

from baselom_core.models import GameRules, GameState, Score


def serialize_state(state: GameState) -> str:
    """Serialize a game state to JSON.

    Args:
        state: The game state to serialize.

    Returns:
        JSON string representation.
    """
    return json.dumps(_state_to_dict(state))


def deserialize_state(json_str: str) -> GameState:
    """Deserialize a game state from JSON.

    Args:
        json_str: JSON string representation.

    Returns:
        Deserialized game state.
    """
    data = json.loads(json_str)
    return _dict_to_state(data)


def _state_to_dict(state: GameState) -> dict[str, Any]:
    """Convert GameState to dictionary."""
    return {
        "inning": state.inning,
        "top": state.top,
        "outs": state.outs,
        "bases": list(state.bases),
        "score": {"home": state.score.home, "away": state.score.away},
        "current_batter_id": state.current_batter_id,
        "current_pitcher_id": state.current_pitcher_id,
    }


def _dict_to_state(data: dict[str, Any]) -> GameState:
    """Convert dictionary to GameState."""
    return GameState(
        inning=data["inning"],
        top=data["top"],
        outs=data["outs"],
        bases=tuple(data["bases"]),
        score=Score(home=data["score"]["home"], away=data["score"]["away"]),
        current_batter_id=data.get("current_batter_id"),
        current_pitcher_id=data.get("current_pitcher_id"),
    )
