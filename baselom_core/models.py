"""Core data models for the baseball game state."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def normalize_lineups(lineups: Mapping[str, tuple[str, ...]]) -> MappingProxyType:
    """Return an immutable copy of the provided lineups."""
    return MappingProxyType({team: tuple(players) for team, players in lineups.items()})


LINEUPS_IMMUTABLE_ERROR = "lineups must be an immutable mapping (MappingProxyType)"
LINEUPS_TUPLE_ERROR = "lineups must contain tuples for each team"
_DEFAULT_LINEUPS = normalize_lineups({"home": (), "away": ()})


def _default_lineups() -> MappingProxyType:
    """Provide empty immutable lineups for initialization."""
    return _DEFAULT_LINEUPS


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
        lineups: Immutable batting orders for home and away teams.
    """

    inning: int
    top: bool
    outs: int
    bases: tuple[str | None, str | None, str | None]
    score: Score
    balls: int = 0
    strikes: int = 0
    current_batter_id: str | None = None
    current_pitcher_id: str | None = None
    lineups: Mapping[str, tuple[str, ...]] = field(
        default_factory=_default_lineups,
    )

    def __post_init__(self) -> None:
        """Validate lineups immutability requirements."""
        if not isinstance(self.lineups, MappingProxyType):
            raise TypeError(LINEUPS_IMMUTABLE_ERROR)
        if not all(isinstance(players, tuple) for players in self.lineups.values()):
            raise TypeError(LINEUPS_TUPLE_ERROR)


@dataclass(frozen=True)
class ValidationResult:
    """Result of state validation."""

    is_valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
