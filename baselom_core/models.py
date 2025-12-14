"""Core data models for the baseball game state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """Score tracking for both teams."""

    home: int = 0
    away: int = 0


@dataclass(frozen=True)
class GameRules:
    """Configurable game rules.

    Attributes:
        designated_hitter: Whether designated hitter is used.
        max_innings: Maximum number of innings (None for unlimited).
        extra_innings_tiebreaker: Extra innings tiebreaker rule.
    """

    designated_hitter: bool = False
    max_innings: int | None = 9
    extra_innings_tiebreaker: str | None = None


@dataclass(frozen=True)
class GameState:
    """Immutable representation of the current game state.

    Attributes:
        inning: 1-based inning number.
        top: True if top of inning (away team batting).
        outs: Number of outs (0-2).
        bases: Base runners (first, second, third).
        score: Current score.
        current_batter_id: ID of current batter.
        current_pitcher_id: ID of current pitcher.
    """

    inning: int
    top: bool
    outs: int
    bases: tuple[str | None, str | None, str | None]
    score: Score
    current_batter_id: str | None = None
    current_pitcher_id: str | None = None
