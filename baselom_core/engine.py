"""FSM engine logic for state transitions."""

from dataclasses import replace

from baselom_core.exceptions import StateError, ValidationError
from baselom_core.models import GameRules, GameState, Score, normalize_lineups
from baselom_core.validators import validate_state

VALID_PITCH_RESULTS = {
    "ball",
    "strike_called",
    "strike_swinging",
    "foul",
    "foul_tip",
}


def _validate_lineup(team: str, lineup: list[str]) -> None:
    if len(lineup) != 9:
        message = f"{team}_lineup must contain exactly 9 players, got {len(lineup)}"
        raise ValidationError(message)
    duplicates = {player for player in lineup if lineup.count(player) > 1}
    if duplicates:
        duplicate = sorted(duplicates)[0]
        message = f"{team}_lineup contains duplicate player '{duplicate}'"
        raise ValidationError(message)


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
    _ = rules  # Will be used in full implementation
    _validate_lineup("home", home_lineup)
    _validate_lineup("away", away_lineup)

    lineups = normalize_lineups({"home": tuple(home_lineup), "away": tuple(away_lineup)})
    batter = away_lineup[0] if away_lineup else None
    pitcher = home_lineup[0] if home_lineup else None

    return GameState(
        inning=1,
        top=True,
        outs=0,
        balls=0,
        strikes=0,
        bases=(None, None, None),
        score=Score(home=0, away=0),
        current_batter_id=batter,
        current_pitcher_id=pitcher,
        lineups=lineups,
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
    _ = rules  # Placeholder for future rule-driven logic
    if pitch_result not in VALID_PITCH_RESULTS:
        raise ValidationError(f"invalid pitch_result '{pitch_result}'")

    validation = validate_state(state)
    if not validation.is_valid:
        raise ValidationError(validation.errors[0])

    if state.outs > 2:
        raise StateError("cannot apply pitch when half-inning is already complete")

    event_type = pitch_result
    new_state = state

    if pitch_result == "ball":
        if state.balls < 3:
            new_state = replace(state, balls=state.balls + 1)
        else:
            new_state = _process_walk(state)
            event_type = "walk"
    elif pitch_result == "foul":
        if state.strikes < 2:
            new_state = replace(state, strikes=state.strikes + 1)
    elif pitch_result == "foul_tip":
        if state.strikes >= 2:
            new_state, event_type = _record_out(state, "strikeout_swinging")
        else:
            new_state = replace(state, strikes=state.strikes + 1)
    else:  # strike_called or strike_swinging
        if state.strikes < 2:
            new_state = replace(state, strikes=state.strikes + 1)
        else:
            suffix = "looking" if pitch_result == "strike_called" else "swinging"
            new_state, event_type = _record_out(state, f"strikeout_{suffix}")

    return new_state, {
        "event_type": event_type,
        "balls": new_state.balls,
        "strikes": new_state.strikes,
        "outs": new_state.outs,
    }


def _record_out(state: GameState, event_type: str) -> tuple[GameState, str]:
    outs = state.outs + 1
    top = state.top
    inning = state.inning
    bases = state.bases

    if outs >= 3:
        outs = 0
        bases = (None, None, None)
        if state.top:
            top = False
        else:
            top = True
            inning = state.inning + 1

    new_state = replace(
        state,
        outs=outs,
        balls=0,
        strikes=0,
        bases=bases,
        top=top,
        inning=inning,
    )
    return new_state, event_type


def _process_walk(state: GameState) -> GameState:
    bases = list(state.bases)
    score = state.score
    runs_scored = 0

    # Forced advance: third -> home, second -> third, first -> second, batter -> first
    if bases[2] is not None:
        runs_scored += 1
    bases[2] = bases[1]
    bases[1] = bases[0]
    bases[0] = state.current_batter_id

    if runs_scored:
        if state.top:
            score = Score(home=score.home, away=score.away + runs_scored)
        else:
            score = Score(home=score.home + runs_scored, away=score.away)

    return replace(state, bases=tuple(bases), balls=0, strikes=0, score=score)
