# Data Models

## Overview

This document specifies all data models used in Baselom Core. All models follow **strict immutability principles** and are designed for deterministic serialization.

## Immutability Requirements

All data models in Baselom are **deeply immutable**:

| Requirement | Description |
|-------------|-------------|
| **Frozen dataclasses** | All dataclasses use `frozen=True` |
| **Immutable containers** | Use `Tuple` instead of `List`, `FrozenDict` instead of `Dict` for nested structures |
| **No mutation methods** | No methods that modify internal state |
| **Copy-on-write** | State changes return new instances |

### Python Implementation

```python
from typing import Tuple, Mapping
from types import MappingProxyType
from dataclasses import dataclass

# Use immutable containers
@dataclass(frozen=True)
class ImmutableExample:
    items: Tuple[str, ...]           # Not List[str]
    metadata: Mapping[str, str]       # Not Dict[str, str]

# Factory function to ensure immutability from construction
def create_immutable_example(
    items: Tuple[str, ...],
    metadata: Mapping[str, str]
) -> ImmutableExample:
    """Create ImmutableExample with guaranteed immutable metadata."""
    immutable_metadata = MappingProxyType(dict(metadata))
    return ImmutableExample(items=items, metadata=immutable_metadata)
```

### Rust Implementation

```rust
// All structs derive Clone but not mutating traits
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct GameState {
    pub inning: u8,
    pub top: bool,
    // Use Vec but treat as immutable (clone for modifications)
    pub bases: [Option<String>; 3],
    // ...
}

impl GameState {
    // All "mutations" return new instances
    pub fn with_outs(&self, outs: u8) -> Self {
        Self {
            outs,
            ..self.clone()
        }
    }
}
```

## Core Models

### GameState

The primary state object representing a complete game snapshot.

#### Definition

```python
from typing import Tuple, Mapping, Optional, Literal, Any
from types import MappingProxyType
from dataclasses import dataclass

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
    
    # Score (Immutable mapping)
    score: Mapping[str, int]
    """Scores by team: {'home': int, 'away': int}. Uses MappingProxyType internally."""
    
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
    
    # Lineup State (Immutable mappings)
    lineup_index: Mapping[str, int]
    """
    Current batting order position per team.
    {'home': 0-8, 'away': 0-8}
    Uses MappingProxyType internally.
    """
    
    lineups: Mapping[str, Tuple[str, ...]]
    """
    Batting order per team.
    {'home': (id1, id2, ..., id9), 'away': (id1, id2, ..., id9)}
    Uses MappingProxyType internally.
    """
    
    # Pitchers (Immutable mapping)
    pitchers: Mapping[str, str]
    """Current pitcher per team: {'home': pitcher_id, 'away': pitcher_id}. Uses MappingProxyType internally."""
    
    # Game Progress (Immutable mapping)
    inning_runs: Mapping[str, int]
    """Runs scored in current half-inning per team. Uses MappingProxyType internally."""
    
    game_status: Literal['in_progress', 'final', 'suspended']
    """Current game status."""
    
    # Event Tracking
    event_history: Tuple[Mapping[str, Any], ...]
    """
    Immutable sequence of event references.
    
    Note: For efficiency, this may store only event_ids rather than full events.
    Full event data is retrieved from the payload store when needed.
    See serialization.md for the Event History Storage Architecture.
    """
    
    # Metadata
    rules_version: str
    """Version identifier for rules applied."""
    
    created_at: str
    """ISO 8601 timestamp of state creation (UTC with Z suffix)."""
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

Immutable record of a game event with **envelope/payload structure**.

#### Event Architecture

Events consist of two parts:

| Part | Purpose | Included in event_id |
|------|---------|---------------------|
| **Envelope** | Metadata (ID, type, timestamps, source) | No (except event_type and schema_version) |
| **Payload** | Essential facts for replay | Yes |

This separation enables:
- Content-based identification (same play = same ID, regardless of timestamp)
- Efficient storage (deduplication by event_id)
- Clear audit trail (envelope stores when/who/where)

#### Event Envelope

```python
@dataclass(frozen=True)
class EventEnvelope:
    """Metadata wrapper for events."""
    
    event_id: str
    """
    Content-based identifier: SHA-256(schema_version|event_type|canonical_json(payload)).
    NOT a UUID - derived from payload content.
    """
    
    event_type: str
    """Event type with version suffix (e.g., 'hit.v1', 'out.v1')."""
    
    schema_version: str
    """Schema version for payload structure (e.g., '1')."""
    
    created_at: str
    """ISO 8601 timestamp (UTC with Z suffix). NOT included in event_id calculation."""
    
    actor: Optional[str] = None
    """Entity that created this event (e.g., 'baselom-engine-v0.9')."""
    
    source: Optional[str] = None
    """Source system identifier (e.g., 'game-server-1')."""
```

#### Base Event Payload

```python
@dataclass(frozen=True)
class EventPayload:
    """Base payload class containing essential facts for replay."""
    
    game_id: str
    """Game identifier."""
    
    inning: int
    """Inning number when event occurred."""
    
    top: bool
    """Half inning (top=True, bottom=False)."""
    
    outs_before: int
    """Outs before the event (0-2)."""
```

#### Complete Event

```python
@dataclass(frozen=True)
class Event:
    """Complete event with envelope and payload."""
    
    envelope: EventEnvelope
    """Event metadata."""
    
    payload: EventPayload  # Or specific payload subclass
    """Event content."""
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
class PitchEventPayload(EventPayload):
    """Payload for pitch events."""
    pitch_result: Literal['ball', 'strike_called', 'strike_swinging', 'foul', 'foul_tip']
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
class HitEventPayload(EventPayload):
    """Payload for hit events.
    
    Note: 'rbi' and 'runners_scored' are NOT stored - they are derived during replay.
    Only essential facts (who hit, where runners moved) are stored.
    """
    hit_type: Literal['single', 'double', 'triple', 'home_run', 'ground_rule_double']
    batter_id: str
    pitcher_id: str
    runner_advances: Tuple[Mapping[str, Any], ...]
    """
    Minimal runner movement info.
    Each entry: {'runner_id': str, 'from_base': int, 'to_base': int}
    from_base: 0=batter, 1-3=bases
    to_base: 1-3=bases, 4=home
    """
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
class OutEventPayload(EventPayload):
    """Payload for out events."""
    out_type: str
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
class WalkEventPayload(EventPayload):
    """Payload for walk/HBP events."""
    walk_type: Literal['walk', 'intentional_walk', 'hit_by_pitch']
    batter_id: str
    pitcher_id: str
    runner_advances: Tuple[Mapping[str, Any], ...]
    """Forced runner advances due to walk. Run scored is derived."""
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
class GameEventPayload(EventPayload):
    """Payload for game management events."""
    event_subtype: str  # 'half_inning_end', 'game_start', etc.
    details: Mapping[str, Any]  # Immutable mapping for event-specific details
```

#### Legacy Event Format (Deprecated)

For backward compatibility, the flat event format is still supported:

```python
@dataclass(frozen=True)
class LegacyEvent:
    """Deprecated flat event format. Use Event with envelope/payload instead."""
    event_type: str
    event_id: str  # UUID in legacy format
    timestamp: str
    inning: int
    top: bool
    outs_before: int
    outs_after: int
    # ... additional fields depending on event type
```

**Migration Note**: Legacy events with UUID-based `event_id` should be migrated to the new format with content-based IDs. See [Serialization - Migration Strategy](./serialization.md#migration-strategy).

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
    """
    Full enumeration of possible game statuses.
    
    Note: GameState.game_status field only uses a subset of these values:
    - 'in_progress': Game is actively being played
    - 'final': Game has completed normally
    - 'suspended': Game was suspended and may be resumed
    
    The additional statuses are used in scheduling and archive contexts:
    - 'not_started': Game has not begun (used in MultiGameArchive scheduling)
    - 'postponed': Game was postponed before starting
    - 'cancelled': Game was cancelled
    """
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    FINAL = 'final'
    SUSPENDED = 'suspended'
    POSTPONED = 'postponed'
    CANCELLED = 'cancelled'
```

**GameState.game_status Valid Values**: Only `'in_progress'`, `'final'`, and `'suspended'` are valid for the `GameState.game_status` field. Other statuses are used for game scheduling and archive metadata.

---

## Type Aliases

```python
from typing import TypeAlias

PlayerId: TypeAlias = str
"""Unique player identifier."""

TeamId: TypeAlias = Literal['home', 'away']
"""Team identifier."""

BaseIndex: TypeAlias = Literal[0, 1, 2]
"""Base index for base state: 0=first, 1=second, 2=third."""

BaseOrHome: TypeAlias = Literal[0, 1, 2, 3]
"""Base index including home plate: 0=first, 1=second, 2=third, 3=home.

Used in runner advancement operations where the destination can be home plate.
This differs from BaseIndex which only represents occupied base positions (0-2).

Example usage:
    runner_advances: Dict[BaseIndex, BaseOrHome]  # from_base -> to_base
    # {0: 2}  means runner on 1st advances to 3rd
    # {2: 3}  means runner on 3rd scores (advances to home)
"""

InningHalf: TypeAlias = Literal['top', 'bottom']
"""Half of an inning."""

Bases: TypeAlias = Tuple[Optional[PlayerId], Optional[PlayerId], Optional[PlayerId]]
"""Base state: (first, second, third)."""
```

---

## Statistics Models

### PlayerBattingStats

Batting statistics for a player.

```python
@dataclass(frozen=True)
class PlayerBattingStats:
    """Batting statistics for a single player."""
    
    player_id: str
    """Player identifier."""
    
    # Plate Appearance Stats
    plate_appearances: int = 0
    """Total plate appearances."""
    
    at_bats: int = 0
    """Official at-bats (PA minus walks, HBP, sacrifices)."""
    
    # Hit Stats
    hits: int = 0
    """Total hits."""
    
    singles: int = 0
    """Number of singles."""
    
    doubles: int = 0
    """Number of doubles."""
    
    triples: int = 0
    """Number of triples."""
    
    home_runs: int = 0
    """Number of home runs."""
    
    # Production Stats
    runs: int = 0
    """Runs scored."""
    
    rbi: int = 0
    """Runs batted in."""
    
    # Discipline Stats
    walks: int = 0
    """Base on balls."""
    
    strikeouts: int = 0
    """Strikeouts."""
    
    hit_by_pitch: int = 0
    """Times hit by pitch."""
    
    # Calculated Properties
    @property
    def batting_average(self) -> float:
        """Calculate batting average (H/AB)."""
        return self.hits / self.at_bats if self.at_bats > 0 else 0.0
    
    @property
    def on_base_percentage(self) -> float:
        """Calculate on-base percentage."""
        total = self.at_bats + self.walks + self.hit_by_pitch
        if total == 0:
            return 0.0
        return (self.hits + self.walks + self.hit_by_pitch) / total
    
    @property
    def slugging_percentage(self) -> float:
        """Calculate slugging percentage."""
        if self.at_bats == 0:
            return 0.0
        total_bases = (self.singles + 2 * self.doubles + 
                      3 * self.triples + 4 * self.home_runs)
        return total_bases / self.at_bats
    
    @property
    def ops(self) -> float:
        """Calculate OPS (OBP + SLG)."""
        return self.on_base_percentage + self.slugging_percentage
```

---

### PlayerPitchingStats

Pitching statistics for a player.

```python
@dataclass(frozen=True)
class PlayerPitchingStats:
    """Pitching statistics for a single player."""
    
    player_id: str
    """Player identifier."""
    
    # Appearance Stats
    games: int = 0
    """Games pitched."""
    
    games_started: int = 0
    """Games started as pitcher."""
    
    innings_pitched: float = 0.0
    """Innings pitched (fractional, e.g., 6.2 = 6 2/3 innings)."""
    
    # Result Stats
    wins: int = 0
    """Wins."""
    
    losses: int = 0
    """Losses."""
    
    saves: int = 0
    """Saves."""
    
    # Performance Stats
    hits_allowed: int = 0
    """Hits allowed."""
    
    runs_allowed: int = 0
    """Runs allowed."""
    
    earned_runs: int = 0
    """Earned runs allowed."""
    
    walks_allowed: int = 0
    """Walks issued."""
    
    strikeouts: int = 0
    """Strikeouts."""
    
    home_runs_allowed: int = 0
    """Home runs allowed."""
    
    # Pitch Count
    pitches_thrown: int = 0
    """Total pitches thrown."""
    
    # Calculated Properties
    @property
    def era(self) -> float:
        """Calculate earned run average."""
        if self.innings_pitched == 0:
            return 0.0
        return (self.earned_runs * 9) / self.innings_pitched
    
    @property
    def whip(self) -> float:
        """Calculate WHIP (Walks + Hits per Inning Pitched)."""
        if self.innings_pitched == 0:
            return 0.0
        return (self.walks_allowed + self.hits_allowed) / self.innings_pitched
    
    @property
    def strikeout_rate(self) -> float:
        """Calculate K/9 (strikeouts per 9 innings)."""
        if self.innings_pitched == 0:
            return 0.0
        return (self.strikeouts * 9) / self.innings_pitched
```

---

### PlayerFieldingStats

Fielding statistics for a player.

```python
@dataclass(frozen=True)
class PlayerFieldingStats:
    """Fielding statistics for a single player."""
    
    player_id: str
    """Player identifier."""
    
    position: str
    """Primary fielding position."""
    
    games: int = 0
    """Games played at position."""
    
    innings: float = 0.0
    """Innings played at position."""
    
    putouts: int = 0
    """Putouts."""
    
    assists: int = 0
    """Assists."""
    
    errors: int = 0
    """Errors committed."""
    
    double_plays: int = 0
    """Double plays participated in."""
    
    @property
    def fielding_percentage(self) -> float:
        """Calculate fielding percentage."""
        total_chances = self.putouts + self.assists + self.errors
        if total_chances == 0:
            return 0.0
        return (self.putouts + self.assists) / total_chances
```

---

### GamePlayerStats

Combined statistics for a player in a single game.

```python
@dataclass(frozen=True)
class GamePlayerStats:
    """Statistics for a player in a single game."""
    
    player_id: str
    """Player identifier."""
    
    game_id: str
    """Game identifier."""
    
    team: Literal['home', 'away']
    """Team the player was on."""
    
    batting: Optional[PlayerBattingStats] = None
    """Batting stats for this game."""
    
    pitching: Optional[PlayerPitchingStats] = None
    """Pitching stats for this game (if applicable)."""
    
    fielding: Optional[PlayerFieldingStats] = None
    """Fielding stats for this game."""
    
    started: bool = False
    """Whether player started the game."""
    
    entered_game: bool = True
    """Whether player entered the game."""
    
    batting_order: Optional[int] = None
    """Position in batting order (0-8, None if didn't bat)."""
```

---

## Roster Models

### PlayerStatus

Status of a player on the roster.

```python
class PlayerStatus(Enum):
    """Status of a player on the roster."""
    
    ACTIVE = 'active'
    """Player is on active roster and available to play."""
    
    BENCH = 'bench'
    """Player is on bench, available as substitute."""
    
    INJURED = 'injured'
    """Player is injured and not available."""
    
    INACTIVE = 'inactive'
    """Player is on inactive list."""
    
    STARTING = 'starting'
    """Player is in starting lineup for current game."""
    
    SUBSTITUTED_OUT = 'substituted_out'
    """Player was substituted out of current game."""
```

---

### Player

Player information and current status.

```python
@dataclass(frozen=True)
class Player:
    """Player information."""
    
    player_id: str
    """Unique player identifier."""
    
    name: str
    """Player display name."""
    
    number: Optional[int] = None
    """Jersey number."""
    
    positions: Tuple[str, ...] = ()
    """Positions player can play (e.g., ('P', 'OF'))."""
    
    bats: Literal['L', 'R', 'S'] = 'R'
    """Batting hand (Left, Right, Switch)."""
    
    throws: Literal['L', 'R'] = 'R'
    """Throwing hand."""
```

---

### RosterEntry

Entry in a team roster.

```python
@dataclass(frozen=True)
class RosterEntry:
    """Entry for a player on a team roster."""
    
    player: Player
    """Player information."""
    
    status: PlayerStatus = PlayerStatus.ACTIVE
    """Current player status."""
    
    current_position: Optional[str] = None
    """Current defensive position (if in game)."""
    
    games_played: int = 0
    """Games played this season."""
    
    season_batting_stats: Optional[PlayerBattingStats] = None
    """Accumulated batting stats for season."""
    
    season_pitching_stats: Optional[PlayerPitchingStats] = None
    """Accumulated pitching stats for season."""
```

---

### Roster

Complete team roster.

```python
@dataclass(frozen=True)
class Roster:
    """Complete roster for a team."""
    
    team_id: str
    """Team identifier."""
    
    team_name: str
    """Team display name."""
    
    players: Tuple[RosterEntry, ...]
    """All players on roster."""
    
    def get_active_players(self) -> Tuple[RosterEntry, ...]:
        """Get players available to play."""
        return tuple(p for p in self.players 
                    if p.status in (PlayerStatus.ACTIVE, PlayerStatus.BENCH))
    
    def get_player(self, player_id: str) -> Optional[RosterEntry]:
        """Get a specific player by ID."""
        for entry in self.players:
            if entry.player.player_id == player_id:
                return entry
        return None
```

---

### SubstitutionRecord

Record of a substitution during a game.

```python
@dataclass(frozen=True)
class SubstitutionRecord:
    """Record of a player substitution."""
    
    game_id: str
    """Game identifier."""
    
    inning: int
    """Inning when substitution occurred."""
    
    top: bool
    """Half of inning."""
    
    team: Literal['home', 'away']
    """Team making substitution."""
    
    player_out_id: str
    """Player removed from game."""
    
    player_in_id: str
    """Player entering game."""
    
    position: str
    """Defensive position."""
    
    batting_order: int
    """Batting order position (0-8)."""
    
    timestamp: str
    """ISO 8601 timestamp."""
```

---

## Multi-Game Archive Models

### GameRecord

Complete record of a single game for archiving.

```python
@dataclass(frozen=True)
class GameRecord:
    """Complete record of a baseball game."""
    
    game_id: str
    """Unique game identifier."""
    
    date: str
    """Game date (ISO 8601 date)."""
    
    home_team: str
    """Home team identifier."""
    
    away_team: str
    """Away team identifier."""
    
    final_state: GameState
    """Final game state."""
    
    events: Tuple[Event, ...]
    """All events in chronological order."""
    
    player_stats: Tuple[GamePlayerStats, ...]
    """Statistics for all players who participated."""
    
    substitutions: Tuple[SubstitutionRecord, ...]
    """All substitutions made during game."""
    
    rules: GameRules
    """Rules used for this game."""
    
    metadata: Dict[str, Any]
    """Additional game metadata (venue, weather, etc.)."""
```

---

### MultiGameArchive

Archive containing multiple games.

```python
@dataclass(frozen=True)
class MultiGameArchive:
    """Archive of multiple baseball games."""
    
    archive_id: str
    """Unique archive identifier."""
    
    name: str
    """Archive name (e.g., '2024 Season', 'Tournament')."""
    
    description: str
    """Archive description."""
    
    games: Tuple[GameRecord, ...]
    """All games in the archive."""
    
    rosters: Dict[str, Roster]
    """Rosters by team_id."""
    
    created_at: str
    """ISO 8601 timestamp of archive creation."""
    
    updated_at: str
    """ISO 8601 timestamp of last update."""
    
    baselom_version: str
    """Baselom version used to create archive."""
    
    def get_games_by_team(self, team_id: str) -> Tuple[GameRecord, ...]:
        """Get all games for a specific team."""
        return tuple(g for g in self.games 
                    if g.home_team == team_id or g.away_team == team_id)
    
    def get_games_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> Tuple[GameRecord, ...]:
        """Get games within a date range."""
        return tuple(g for g in self.games 
                    if start_date <= g.date <= end_date)
```

---

### SeasonStats

Aggregated statistics for a season or period.

```python
@dataclass(frozen=True)
class SeasonStats:
    """Aggregated statistics across multiple games."""
    
    player_id: str
    """Player identifier."""
    
    period_name: str
    """Name of period (e.g., '2024 Season', 'June 2024')."""
    
    games_played: int
    """Total games played."""
    
    batting: PlayerBattingStats
    """Aggregated batting statistics."""
    
    pitching: Optional[PlayerPitchingStats] = None
    """Aggregated pitching statistics (if applicable)."""
    
    fielding: Optional[PlayerFieldingStats] = None
    """Aggregated fielding statistics."""
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
