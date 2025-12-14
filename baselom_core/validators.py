"""State validation rules."""

from baselom_core.models import GameState, ValidationResult

MAX_OUTS = 2
MAX_BALLS = 3
MAX_STRIKES = 2
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

    if state.balls < 0 or state.balls > MAX_BALLS:
        errors.append(f"balls must be in range [0, {MAX_BALLS}], got {state.balls}")

    if state.strikes < 0 or state.strikes > MAX_STRIKES:
        errors.append(
            f"strikes must be in range [0, {MAX_STRIKES}], got {state.strikes}",
        )

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

        seen: set[str] = set()
        duplicates: set[str] = set()
        for player in lineup:
            if player in seen:
                duplicates.add(player)
            else:
                seen.add(player)
        duplicates = sorted(duplicates)
        errors.extend(
            f"duplicate player '{duplicate}' in {team} lineup" for duplicate in duplicates
        )

    # Duplicate runners on bases are not allowed
    seen_bases: set[str] = set()
    for runner in state.bases:
        if runner is None:
            continue
        if runner in seen_bases:
            errors.append(f"duplicate runner '{runner}' found on multiple bases")
        else:
            seen_bases.add(runner)

    return ValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
