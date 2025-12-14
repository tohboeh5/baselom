"""State validation rules."""

from collections import Counter

from baselom_core.models import GameState, ValidationResult

MAX_OUTS = 2
MIN_INNING = 1
LINEUP_SIZE = 9


def validate_state(state: GameState) -> ValidationResult:
    """Validate that a game state is consistent.

    Args:
        state: The game state to validate.

    Returns:
        ValidationResult: Validation result containing errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if state.outs < 0 or state.outs > MAX_OUTS:
        errors.append(f"outs must be in range [0, {MAX_OUTS}], got {state.outs}")

    if state.inning < MIN_INNING:
        errors.append(f"inning must be >= {MIN_INNING}, got {state.inning}")

    if state.score.home < 0 or state.score.away < 0:
        scores = {"home": state.score.home, "away": state.score.away}
        errors.append(f"scores must be non-negative, got {scores}")

    for team in ("home", "away"):
        lineup = state.lineups.get(team, ())
        count = len(lineup)
        if count != LINEUP_SIZE:
            errors.append(
                f"lineup must contain exactly {LINEUP_SIZE} players, got {count} for {team}",
            )

        duplicates = sorted(
            player for player, count in Counter(lineup).items() if count > 1
        )
        errors.extend(
            f"duplicate player '{duplicate}' in {team} lineup" for duplicate in duplicates
        )

    return ValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
