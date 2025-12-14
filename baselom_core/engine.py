"""FSM engine logic for state transitions."""

from baselom_core.models import GameRules, GameState, Score


def initial_game_state(
    home_lineup: list[str],
    away_lineup: list[str],
    rules: GameRules,
) -> GameState:
    """Create an initial game state.

    Args:
        home_lineup: List of player IDs for home team lineup.
        away_lineup: List of player IDs for away team lineup.
        rules: Game rules configuration.

    Returns:
        Initial game state ready for the first pitch.
    """
    _ = home_lineup, away_lineup, rules  # Will be used in full implementation
    return GameState(
        inning=1,
        top=True,
        outs=0,
        bases=(None, None, None),
        score=Score(home=0, away=0),
    )


def apply_pitch(
    state: GameState,
    pitch_result: str,
    rules: GameRules,
) -> tuple[GameState, dict[str, object]]:
    """Apply a pitch result to the game state.

    Args:
        state: Current game state.
        pitch_result: The pitch outcome ('ball', 'strike', etc.).
        rules: Game rules configuration.

    Returns:
        Tuple of (new_state, event).

    Raises:
        ValidationError: If inputs are invalid.
        StateError: If game has ended.
    """
    _ = state, pitch_result, rules  # Will be used in full implementation
    message = "apply_pitch not yet implemented"
    raise NotImplementedError(message)
