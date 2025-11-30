# Data Models

## Overview

This document specifies all data models used in Baselom Core. All models follow immutability principles and are designed for serialization.

## Core Models

### GameState

The primary state object representing a complete game snapshot.

#### Definition

```python
@dataclass(frozen=True)
class GameState:
    """Immutable representation of baseball game state."""
    
    # Inning Information
    inning: int
    """1-based inning number (1, 2, 3, ...)."""
    
    top: bool
    """True if top of inning (away batting), False if bottom (home batting)."""
    
    # Count State
    outs: int
    """Number of outs in current half-inning (0, 1, or 2)."""
    
    balls: int
    """Current ball count (0-3)."""
    
    strikes: int
    """Current strike count (0-2)."""
    
    # Base State
    bases: Tuple[Optional[str], Optional[str], Optional[str]]
    """
    Runner IDs on bases: (first, second, third).
    None indicates empty base.
    """
    
    # Score
    score: Dict[str, int]
    """Scores by team: {'home': int, 'away': int}."""
    
    # Team Context
    batting_team: Literal['home', 'away']
    """Currently batting team."""
    
    fielding_team: Literal['home', 'away']
    """Currently fielding team."""
    
    # Player Context
    current_pitcher_id: Optional[str]
    """Active pitcher's player ID."""
    
    current_batter_id: Optional[str]
    """Active batter's player ID."""
    
    # Lineup State
    lineup_index: Dict[str, int]
    """
    Current batting order position per team.
    {'home': 0-8, 'away': 0-8}
    """
    
    lineups: Dict[str, Tuple[str, ...]]
    """
    Batting order per team.
    {'home': (id1, id2, ..., id9), 'away': (id1, id2, ..., id9)}
    """
    
    # Pitchers
    pitchers: Dict[str, str]
    """Current pitcher per team: {'home': pitcher_id, 'away': pitcher_id}."""
    
    # Game Progress
    inning_runs: Dict[str, int]
    """Runs scored in current half-inning per team."""
    
    game_status: Literal['in_progress', 'final', 'suspended']
    """Current game status."""
    
    # Event Tracking
    event_history: Tuple[Dict[str, Any], ...]
    """Immutable sequence of all events in the game."""
    
    # Metadata
    rules_version: str
    """Version identifier for rules applied."""
    
    created_at: str
    """ISO 8601 timestamp of state creation."""
```

#### Field Constraints

| Field | Type | Valid Range | Notes |
|-------|------|-------------|-------|
| `inning` | int | ≥ 1 | Increases monotonically |
| `top` | bool | True/False | Alternates each half-inning |
| `outs` | int | 0, 1, 2 | Resets at half-inning |
| `balls` | int | 0, 1, 2, 3 | Resets on plate appearance end |
| `strikes` | int | 0, 1, 2 | Resets on plate appearance end |
| `bases` | tuple | 3 elements | None = empty base |
| `score.home` | int | ≥ 0 | Monotonically increasing |
| `score.away` | int | ≥ 0 | Monotonically increasing |
| `lineup_index.*` | int | 0-8 | Wraps around |

#### Example

```python
GameState(
    inning=3,
    top=False,
    outs=1,
    balls=2,
    strikes=1,
    bases=('player_42', None, 'player_17'),
    score={'home': 2, 'away': 3},
    batting_team='home',
    fielding_team='away',
    current_pitcher_id='pitcher_99',
    current_batter_id='batter_05',
    lineup_index={'home': 4, 'away': 2},
    lineups={
        'home': ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'),
        'away': ('a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9')
    },
    pitchers={'home': 'p_home', 'away': 'p_away'},
    inning_runs={'home': 0, 'away': 0},
    game_status='in_progress',
    event_history=(),
    rules_version='1.0.0',
    created_at='2024-01-15T10:30:00Z'
)
```

---

### GameRules

Configuration object for rule variations.

#### Definition

```python
@dataclass(frozen=True)
class GameRules:
    """Configurable baseball rule set."""
    
    # Basic Rules
    designated_hitter: bool = False
    """Enable designated hitter (DH) rule."""
    
    max_innings: Optional[int] = 9
    """Maximum regulation innings. None = unlimited."""
    
    # Extra Innings
    extra_innings_tiebreaker: Optional[str] = None
    """
    Extra innings tiebreaker rule.
    Options: None, 'runner_on_second', 'runner_on_first_and_second'
    """
    
    max_extra_innings: Optional[int] = None
    """Maximum extra innings allowed. None = unlimited."""
    
    # Mercy Rule
    mercy_rule_enabled: bool = False
    """Enable mercy rule (run differential limit)."""
    
    mercy_rule_threshold: int = 10
    """Run differential for mercy rule to apply."""
    
    mercy_rule_min_inning: int = 5
    """Minimum inning for mercy rule to apply."""
    
    # Pitch Rules
    allow_balks: bool = True
    """Enable balk rule."""
    
    allow_wild_pitch: bool = True
    """Enable wild pitch events."""
    
    allow_passed_ball: bool = True
    """Enable passed ball events."""
    
    # Base Running
    runner_advances_on_error: bool = True
    """Allow runner advancement on errors."""
    
    allow_stealing: bool = True
    """Allow base stealing."""
    
    # Substitution Rules
    double_switch_allowed: bool = True
    """Allow double switch substitutions."""
    
    reentry_allowed: bool = False
    """Allow players to re-enter after substitution."""
    
    # Pitcher Rules
    pitcher_spot_dh: bool = False
    """DH can bat in pitcher's spot."""
    
    minimum_pitches_per_batter: int = 1
    """Minimum pitches required before substitution (save situations)."""
    
    # Validation
    strict_mode: bool = True
    """Enable strict validation of all inputs."""
```

#### Rule Presets

```python
# MLB Rules (2024)
MLB_RULES = GameRules(
    designated_hitter=True,  # Universal DH since 2022
    max_innings=9,
    extra_innings_tiebreaker='runner_on_second',  # Since 2020
    max_extra_innings=None,
    mercy_rule_enabled=False
)

# Little League Rules
LITTLE_LEAGUE_RULES = GameRules(
    designated_hitter=False,
    max_innings=6,
    extra_innings_tiebreaker=None,
    mercy_rule_enabled=True,
    mercy_rule_threshold=10,
    mercy_rule_min_inning=4
)

# Classic Rules (No DH, No Tiebreaker)
CLASSIC_RULES = GameRules(
    designated_hitter=False,
    max_innings=9,
    extra_innings_tiebreaker=None,
    mercy_rule_enabled=False
)
```

---

### Event

Immutable record of a game event.

#### Base Event Structure

```python
@dataclass(frozen=True)
class Event:
    """Base event class for all game events."""
    
    event_type: str
    """Event type identifier."""
    
    event_id: str
    """Unique event identifier (UUID)."""
    
    timestamp: str
    """ISO 8601 timestamp."""
    
    inning: int
    """Inning number when event occurred."""
    
    top: bool
    """Half inning (top/bottom)."""
    
    outs_before: int
    """Outs before the event."""
    
    outs_after: int
    """Outs after the event."""
```

#### Event Types

##### Pitch Events

| Type | Description |
|------|-------------|
| `ball` | Ball called |
| `strike_called` | Called strike |
| `strike_swinging` | Swinging strike |
| `foul` | Foul ball |
| `foul_tip` | Foul tip |

```python
@dataclass(frozen=True)
class PitchEvent(Event):
    event_type: Literal['ball', 'strike_called', 'strike_swinging', 'foul', 'foul_tip']
    pitcher_id: str
    batter_id: str
    balls_after: int
    strikes_after: int
    pitch_sequence_number: int
```

##### Hit Events

| Type | Description |
|------|-------------|
| `single` | Single |
| `double` | Double |
| `triple` | Triple |
| `home_run` | Home run |
| `ground_rule_double` | Ground rule double |

```python
@dataclass(frozen=True)
class HitEvent(Event):
    event_type: Literal['single', 'double', 'triple', 'home_run', 'ground_rule_double']
    batter_id: str
    pitcher_id: str
    rbi: int
    runners_scored: Tuple[str, ...]
    runners_advanced: Tuple[Dict[str, Any], ...]
```

##### Out Events

| Type | Description |
|------|-------------|
| `strikeout_swinging` | Strikeout swinging |
| `strikeout_looking` | Strikeout looking |
| `ground_out` | Ground out |
| `fly_out` | Fly out |
| `line_out` | Line out |
| `pop_out` | Pop out |
| `double_play` | Double play |
| `triple_play` | Triple play |
| `force_out` | Force out |
| `tag_out` | Tag out |

```python
@dataclass(frozen=True)
class OutEvent(Event):
    event_type: str
    batter_id: str
    pitcher_id: str
    fielders: Tuple[str, ...]
    runners_out: Tuple[str, ...]
    is_sacrifice: bool
```

##### Walk/HBP Events

| Type | Description |
|------|-------------|
| `walk` | Base on balls |
| `intentional_walk` | Intentional walk |
| `hit_by_pitch` | Hit by pitch |

```python
@dataclass(frozen=True)
class WalkEvent(Event):
    event_type: Literal['walk', 'intentional_walk', 'hit_by_pitch']
    batter_id: str
    pitcher_id: str
    runners_advanced: Tuple[Dict[str, Any], ...]
    run_scored: bool
```

##### Base Running Events

| Type | Description |
|------|-------------|
| `stolen_base` | Stolen base |
| `caught_stealing` | Caught stealing |
| `wild_pitch` | Wild pitch |
| `passed_ball` | Passed ball |
| `balk` | Balk |
| `pickoff` | Pickoff |

```python
@dataclass(frozen=True)
class BaseRunningEvent(Event):
    event_type: str
    runner_id: str
    from_base: int
    to_base: Optional[int]
    is_out: bool
```

##### Game Events

| Type | Description |
|------|-------------|
| `half_inning_end` | End of half inning |
| `inning_end` | End of full inning |
| `game_start` | Game started |
| `game_end` | Game ended |
| `substitution` | Player substitution |

```python
@dataclass(frozen=True)
class GameEvent(Event):
    event_type: str
    details: Dict[str, Any]
```

---

### Lineup

Batting order representation.

```python
@dataclass(frozen=True)
class Lineup:
    """Batting order for a team."""
    
    players: Tuple[str, str, str, str, str, str, str, str, str]
    """Nine player IDs in batting order."""
    
    pitcher_batting_order: Optional[int] = None
    """
    Position in batting order where pitcher bats (0-8).
    None if DH is used.
    """
    
    dh_id: Optional[str] = None
    """Designated hitter player ID, if applicable."""
```

---

### SubstitutionRequest

Request for a player substitution.

```python
@dataclass(frozen=True)
class SubstitutionRequest:
    """Request to substitute a player."""
    
    team: Literal['home', 'away']
    """Team making the substitution."""
    
    player_out: str
    """Player ID being removed."""
    
    player_in: str
    """Player ID entering the game."""
    
    position: Optional[int] = None
    """
    Batting order position (0-8) for the new player.
    If None, inherits from replaced player.
    """
    
    is_double_switch: bool = False
    """Whether this is part of a double switch."""
    
    double_switch_partner: Optional['SubstitutionRequest'] = None
    """The other substitution in a double switch."""
```

---

### ValidationResult

Result of state validation.

```python
@dataclass(frozen=True)
class ValidationResult:
    """Result of state validation."""
    
    is_valid: bool
    """True if state is valid."""
    
    errors: Tuple[str, ...]
    """List of validation error messages."""
    
    warnings: Tuple[str, ...]
    """List of validation warnings."""
```

---

## Enumerations

### PitchResult

Possible outcomes of a pitch.

```python
class PitchResult(Enum):
    BALL = 'ball'
    STRIKE_CALLED = 'strike_called'
    STRIKE_SWINGING = 'strike_swinging'
    FOUL = 'foul'
    FOUL_TIP = 'foul_tip'
    IN_PLAY = 'in_play'
    HIT_BY_PITCH = 'hit_by_pitch'
```

### BattedBallResult

Possible outcomes when ball is put in play.

```python
class BattedBallResult(Enum):
    # Hits
    SINGLE = 'single'
    DOUBLE = 'double'
    TRIPLE = 'triple'
    HOME_RUN = 'home_run'
    
    # Outs
    GROUND_OUT = 'ground_out'
    FLY_OUT = 'fly_out'
    LINE_OUT = 'line_out'
    POP_OUT = 'pop_out'
    
    # Special
    FIELDERS_CHOICE = 'fielders_choice'
    ERROR = 'error'
    DOUBLE_PLAY = 'double_play'
    TRIPLE_PLAY = 'triple_play'
    SACRIFICE_FLY = 'sacrifice_fly'
    SACRIFICE_BUNT = 'sacrifice_bunt'
```

### GameStatus

```python
class GameStatus(Enum):
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    FINAL = 'final'
    SUSPENDED = 'suspended'
    POSTPONED = 'postponed'
    CANCELLED = 'cancelled'
```

---

## Type Aliases

```python
from typing import TypeAlias

PlayerId: TypeAlias = str
"""Unique player identifier."""

TeamId: TypeAlias = Literal['home', 'away']
"""Team identifier."""

BaseIndex: TypeAlias = Literal[0, 1, 2]
"""Base index: 0=first, 1=second, 2=third."""

InningHalf: TypeAlias = Literal['top', 'bottom']
"""Half of an inning."""

Bases: TypeAlias = Tuple[Optional[PlayerId], Optional[PlayerId], Optional[PlayerId]]
"""Base state: (first, second, third)."""
```

---

## JSON Schema

All models can be serialized to JSON. See [Serialization](./serialization.md) for detailed JSON schemas.

### GameState JSON Example

```json
{
  "inning": 3,
  "top": false,
  "outs": 1,
  "balls": 2,
  "strikes": 1,
  "bases": ["player_42", null, "player_17"],
  "score": {
    "home": 2,
    "away": 3
  },
  "batting_team": "home",
  "fielding_team": "away",
  "current_pitcher_id": "pitcher_99",
  "current_batter_id": "batter_05",
  "lineup_index": {
    "home": 4,
    "away": 2
  },
  "lineups": {
    "home": ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9"],
    "away": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9"]
  },
  "pitchers": {
    "home": "p_home",
    "away": "p_away"
  },
  "inning_runs": {
    "home": 0,
    "away": 0
  },
  "game_status": "in_progress",
  "event_history": [],
  "rules_version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## See Also

- [Architecture](./architecture.md) - System design overview
- [API Reference](./api-reference.md) - Function signatures and usage
- [Serialization](./serialization.md) - JSON format specifications
