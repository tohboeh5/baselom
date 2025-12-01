# API Reference

## Overview

This document provides complete API reference for all public functions in Baselom Core.

## Core Functions

### initial_game_state

Create an initial game state.

#### Signature

```python
def initial_game_state(
    home_lineup: List[str],
    away_lineup: List[str],
    rules: GameRules,
    home_pitcher: Optional[str] = None,
    away_pitcher: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> GameState
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `home_lineup` | `List[str]` | Yes | 9 player IDs for home team batting order |
| `away_lineup` | `List[str]` | Yes | 9 player IDs for away team batting order |
| `rules` | `GameRules` | Yes | Rule configuration |
| `home_pitcher` | `str` | No | Home team starting pitcher ID |
| `away_pitcher` | `str` | No | Away team starting pitcher ID |
| `metadata` | `Dict` | No | Additional game metadata |

#### Returns

`GameState` - Initial game state with:
- Inning 1, top
- 0 outs, 0 balls, 0 strikes
- Empty bases
- Score 0-0
- First batter in away lineup ready

#### Raises

| Exception | Condition |
|-----------|-----------|
| `ValidationError` | Invalid lineup (not exactly 9 players) |
| `ValidationError` | Duplicate player IDs in lineup |

#### Example

```python
from baselom_core import initial_game_state, GameRules

rules = GameRules(designated_hitter=True)
state = initial_game_state(
    home_lineup=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'],
    away_lineup=['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
    rules=rules,
    home_pitcher='hp',
    away_pitcher='ap'
)

assert state.inning == 1
assert state.top == True
assert state.batting_team == 'away'
```

---

### apply_pitch

Process a pitch result and return new state with event.

#### Signature

```python
def apply_pitch(
    state: GameState,
    pitch_result: Union[str, PitchResult],
    rules: GameRules,
    batted_ball_result: Optional[Union[str, BattedBallResult]] = None,
    runner_advances: Optional[Dict[int, int]] = None
) -> Tuple[GameState, Event]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | Current game state |
| `pitch_result` | `str` or `PitchResult` | Yes | Pitch outcome |
| `rules` | `GameRules` | Yes | Rule configuration |
| `batted_ball_result` | `str` or `BattedBallResult` | No | Result if ball is in play |
| `runner_advances` | `Dict[int, int]` | No | Manual runner advancement {from_base: to_base} using 0-based indices (0=1st, 1=2nd, 2=3rd, 3=home) |

#### Pitch Results

| Value | Description |
|-------|-------------|
| `'ball'` | Ball called |
| `'strike_called'` | Called strike |
| `'strike_swinging'` | Swinging strike |
| `'foul'` | Foul ball (strike if < 2 strikes) |
| `'foul_tip'` | Foul tip |
| `'in_play'` | Ball put in play (requires `batted_ball_result`) |
| `'hit_by_pitch'` | Batter hit by pitch |

#### Returns

`Tuple[GameState, Event]` - New state and the generated event.

#### State Transitions

| Current | Pitch Result | New State |
|---------|--------------|-----------|
| 0-2 count | Ball | 1-2 count |
| 3-x count | Ball | Walk (batter to first) |
| x-0 count | Strike | x-1 count |
| x-2 count | Strike (not foul) | Strikeout |
| Any | In play hit | Runners advance, new batter |
| Any | In play out | Outs increase, possibly new batter |

#### Raises

| Exception | Condition |
|-----------|-----------|
| `StateError` | Game already ended |
| `ValidationError` | Invalid pitch result |
| `ValidationError` | `in_play` without `batted_ball_result` |

#### Example

```python
# Process a ball
state, event = apply_pitch(state, 'ball', rules)
assert state.balls == 1
assert event.event_type == 'ball'

# Process a single
state, event = apply_pitch(
    state, 
    'in_play', 
    rules,
    batted_ball_result='single'
)
assert state.bases[0] == state.current_batter_id
assert event.event_type == 'single'
```

---

### apply_batter_action

Process a batter or runner action.

#### Signature

```python
def apply_batter_action(
    state: GameState,
    action: str,
    rules: GameRules,
    runner_id: Optional[str] = None,
    target_base: Optional[int] = None
) -> Tuple[GameState, Event]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | Current game state |
| `action` | `str` | Yes | Action type |
| `rules` | `GameRules` | Yes | Rule configuration |
| `runner_id` | `str` | No | Runner performing action (for stealing) |
| `target_base` | `int` | No | Target base (0=first, 1=second, 2=third, 3=home) |

#### Action Types

| Action | Description |
|--------|-------------|
| `'steal'` | Attempt to steal base |
| `'caught_stealing'` | Caught stealing (out) |
| `'advance_on_wild_pitch'` | Runner advances on wild pitch |
| `'advance_on_passed_ball'` | Runner advances on passed ball |
| `'advance_on_balk'` | Runner advances on balk |

#### Returns

`Tuple[GameState, Event]` - New state and generated event.

#### Example

```python
# Stolen base attempt (successful)
state, event = apply_batter_action(
    state,
    'steal',
    rules,
    runner_id='runner_1',
    target_base=2
)
assert event.event_type == 'stolen_base'

# Caught stealing
state, event = apply_batter_action(
    state,
    'caught_stealing',
    rules,
    runner_id='runner_1',
    target_base=2
)
assert state.outs == previous_outs + 1
```

---

### force_substitution

Execute a player substitution.

#### Signature

```python
def force_substitution(
    state: GameState,
    request: SubstitutionRequest,
    rules: GameRules
) -> Tuple[GameState, Event]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | Current game state |
| `request` | `SubstitutionRequest` | Yes | Substitution details |
| `rules` | `GameRules` | Yes | Rule configuration |

#### Returns

`Tuple[GameState, Event]` - New state with substitution applied.

#### Substitution Rules

1. Substituted player cannot return (unless `reentry_allowed` rule)
2. New player takes same batting order position (unless specified)
3. Pitcher substitution must follow minimum batter requirement
4. Double switch allowed if rule enabled

#### Raises

| Exception | Condition |
|-----------|-----------|
| `RuleViolation` | Player already in game |
| `RuleViolation` | Invalid double switch configuration |
| `RuleViolation` | Pitcher minimum batters not met |

#### Example

```python
from baselom_core import force_substitution, SubstitutionRequest

request = SubstitutionRequest(
    team='home',
    player_out='pitcher_1',
    player_in='pitcher_2'
)
state, event = force_substitution(state, request, rules)
assert state.pitchers['home'] == 'pitcher_2'
```

---

### end_half_inning

Explicitly end the current half-inning.

#### Signature

```python
def end_half_inning(
    state: GameState,
    rules: GameRules
) -> Tuple[GameState, Event]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | Current game state |
| `rules` | `GameRules` | Yes | Rule configuration |

#### Returns

`Tuple[GameState, Event]` - New state with:
- Inning/half updated
- Outs reset to 0
- Bases cleared
- Teams swapped

#### Note

This is typically called automatically when 3 outs occur. Manual call is for special situations.

#### Example

```python
state, event = end_half_inning(state, rules)
assert state.outs == 0
assert state.bases == (None, None, None)
```

---

### validate_state

Validate game state consistency.

#### Signature

```python
def validate_state(
    state: GameState,
    rules: Optional[GameRules] = None
) -> ValidationResult
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | State to validate |
| `rules` | `GameRules` | No | Rules for validation context |

#### Returns

`ValidationResult` with:
- `is_valid`: Boolean validity
- `errors`: List of error messages
- `warnings`: List of warning messages

#### Validation Checks

| Check | Error Condition |
|-------|-----------------|
| Outs range | `outs < 0` or `outs > 2` |
| Balls range | `balls < 0` or `balls > 3` |
| Strikes range | `strikes < 0` or `strikes > 2` |
| Inning validity | `inning < 1` |
| Score validity | Negative scores |
| Lineup size | Not exactly 9 players |
| Duplicate players | Same player on multiple bases |
| Team consistency | `batting_team` != opposite of `fielding_team` |

#### Example

```python
result = validate_state(state, rules)
if not result.is_valid:
    for error in result.errors:
        print(f"Validation error: {error}")
```

---

### check_game_end

Check if the game should end.

#### Signature

```python
def check_game_end(
    state: GameState,
    rules: GameRules
) -> Tuple[bool, Optional[str]]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `GameState` | Yes | Current game state |
| `rules` | `GameRules` | Yes | Rule configuration |

#### Returns

`Tuple[bool, Optional[str]]`:
- `(True, 'home')` - Home team wins
- `(True, 'away')` - Away team wins
- `(True, None)` - Tie (suspended)
- `(False, None)` - Game continues

#### End Conditions

| Condition | Description |
|-----------|-------------|
| Regulation complete | 9+ innings, one team ahead after bottom of inning |
| Walk-off | Home team takes lead in bottom of 9th or later |
| Mercy rule | Run differential exceeds threshold |
| Max innings | `max_extra_innings` reached with tie |

#### Example

```python
game_ended, winner = check_game_end(state, rules)
if game_ended:
    if winner:
        print(f"Game over! {winner} wins!")
    else:
        print("Game suspended (tie)")
```

---

## Serialization Functions

### serialize_state

Convert GameState to JSON-serializable dictionary.

#### Signature

```python
def serialize_state(state: GameState) -> Dict[str, Any]
```

#### Example

```python
data = serialize_state(state)
json_str = json.dumps(data)
```

---

### deserialize_state

Create GameState from dictionary.

#### Signature

```python
def deserialize_state(data: Dict[str, Any]) -> GameState
```

#### Raises

| Exception | Condition |
|-----------|-----------|
| `DeserializationError` | Invalid data format |
| `ValidationError` | Data fails validation |

#### Example

```python
data = json.loads(json_str)
state = deserialize_state(data)
```

---

### serialize_event

Convert Event to JSON-serializable dictionary.

#### Signature

```python
def serialize_event(event: Event) -> Dict[str, Any]
```

---

### serialize_rules

Convert GameRules to dictionary.

#### Signature

```python
def serialize_rules(rules: GameRules) -> Dict[str, Any]
```

---

### deserialize_rules

Create GameRules from dictionary.

#### Signature

```python
def deserialize_rules(data: Dict[str, Any]) -> GameRules
```

---

## Utility Functions

### get_next_batter

Get the next batter ID from lineup.

#### Signature

```python
def get_next_batter(state: GameState) -> str
```

---

### get_runners_on_base

Get list of runner IDs currently on base.

#### Signature

```python
def get_runners_on_base(state: GameState) -> List[Tuple[int, str]]
```

#### Returns

List of `(base_index, player_id)` tuples.

---

### calculate_rbi

Calculate RBIs for a play.

#### Signature

```python
def calculate_rbi(
    runners_scored: List[str],
    is_error: bool = False,
    is_ground_into_double_play: bool = False
) -> int
```

---

### get_game_summary

Generate game summary statistics.

#### Signature

```python
def get_game_summary(state: GameState) -> Dict[str, Any]
```

#### Returns

```python
{
    'final_score': {'home': int, 'away': int},
    'innings_played': int,
    'total_events': int,
    'hits': {'home': int, 'away': int},
    'errors': {'home': int, 'away': int},
    'winner': Optional[str]
}
```

---

## Serialization and Hashing Functions

### canonical_json_bytes

Convert a payload to canonical JSON bytes (RFC 8785 compliant).

#### Signature

```python
def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `payload` | `Mapping[str, Any]` | Yes | Data structure to serialize |

#### Returns

`bytes` - Canonical JSON bytes with sorted keys and no whitespace.

#### Example

```python
payload = {'zebra': 1, 'apple': 2}
result = canonical_json_bytes(payload)
# Result: b'{"apple":2,"zebra":1}'
```

---

### generate_event_id

Generate a content-based event ID from payload.

#### Signature

```python
def generate_event_id(
    payload: Mapping[str, Any],
    event_type: str,
    schema_version: str
) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `payload` | `Mapping[str, Any]` | Yes | Event payload (excluding timestamps and ID) |
| `event_type` | `str` | Yes | Event type (e.g., 'hit.v1') |
| `schema_version` | `str` | Yes | Schema version (e.g., '1') |

#### Returns

`str` - SHA-256 hex digest (64 characters).

#### Algorithm

```
event_id = SHA-256(schema_version + "|" + event_type + "|" + canonical_json(payload))
```

#### Example

```python
payload = {'game_id': 'g1', 'inning': 1, 'top': True, 'batter_id': 'p1'}
event_id = generate_event_id(payload, 'hit.v1', '1')
# Result: 'a7b3c2d1...' (64 hex characters)
```

---

### normalize_state

Remove time-like fields from state for comparison.

#### Signature

```python
def normalize_state(state: Mapping[str, Any]) -> dict
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `Mapping[str, Any]` | Yes | State to normalize |

#### Returns

`dict` - State with time fields (`created_at`, `updated_at`, etc.) removed recursively.

#### Example

```python
state = {'inning': 1, 'outs': 0, 'created_at': '2024-01-01T10:00:00Z'}
normalized = normalize_state(state)
# Result: {'inning': 1, 'outs': 0}
```

---

### state_hash

Compute hash of normalized state for comparison.

#### Signature

```python
def state_hash(state: Mapping[str, Any]) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state` | `Mapping[str, Any]` | Yes | State to hash |

#### Returns

`str` - SHA-256 hex digest of normalized, canonicalized state.

#### Example

```python
hash1 = state_hash(state1)
hash2 = state_hash(state2)
if hash1 == hash2:
    print("States are semantically identical")
```

---

### states_equal_ignoring_time

Check if two states are semantically equal (ignoring timestamps).

#### Signature

```python
def states_equal_ignoring_time(
    state1: Mapping[str, Any],
    state2: Mapping[str, Any]
) -> bool
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `state1` | `Mapping[str, Any]` | Yes | First state |
| `state2` | `Mapping[str, Any]` | Yes | Second state |

#### Returns

`bool` - True if states are semantically equal (ignoring time fields).

#### Example

```python
# Different timestamps, same game state
state1 = {'inning': 5, 'outs': 2, 'created_at': '2024-01-01T10:00:00Z'}
state2 = {'inning': 5, 'outs': 2, 'created_at': '2024-01-01T15:30:00Z'}

assert states_equal_ignoring_time(state1, state2)  # True
```

---

## Statistics Functions

### calculate_batting_average

Calculate batting average for a player.

#### Signature

```python
def calculate_batting_average(
    hits: int,
    at_bats: int
) -> float
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hits` | `int` | Yes | Total number of hits |
| `at_bats` | `int` | Yes | Total at-bats (excludes walks, HBP, sacrifices) |

#### Returns

`float` - Batting average (0.0 to 1.0). Returns 0.0 if at_bats is 0.

#### Example

```python
avg = calculate_batting_average(hits=35, at_bats=100)
print(f"{avg:.3f}")  # 0.350
```

---

### calculate_era

Calculate earned run average for a pitcher.

#### Signature

```python
def calculate_era(
    earned_runs: int,
    innings_pitched: float
) -> float
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `earned_runs` | `int` | Yes | Total earned runs allowed |
| `innings_pitched` | `float` | Yes | Innings pitched (e.g., 6.2 for 6⅔ innings) |

#### Returns

`float` - ERA (earned runs per 9 innings). Returns 0.0 if innings_pitched is 0.

#### Example

```python
era = calculate_era(earned_runs=25, innings_pitched=90.0)
print(f"{era:.2f}")  # 2.50
```

---

### calculate_player_stats

Generate comprehensive statistics for a player from game events.

#### Signature

```python
def calculate_player_stats(
    player_id: str,
    events: List[Event],
    stat_type: Literal['batting', 'pitching', 'fielding', 'all'] = 'all'
) -> Union[PlayerBattingStats, PlayerPitchingStats, PlayerFieldingStats, GamePlayerStats]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | `str` | Yes | Player identifier |
| `events` | `List[Event]` | Yes | List of game events to analyze |
| `stat_type` | `str` | No | Type of stats to calculate |

#### Returns

Statistics object based on `stat_type`:
- `'batting'`: `PlayerBattingStats`
- `'pitching'`: `PlayerPitchingStats`
- `'fielding'`: `PlayerFieldingStats`
- `'all'`: `GamePlayerStats` with all applicable stats

#### Example

```python
batting_stats = calculate_player_stats(
    player_id='player_42',
    events=game_state.event_history,
    stat_type='batting'
)
print(f"AVG: {batting_stats.batting_average:.3f}")
print(f"OPS: {batting_stats.ops:.3f}")
```

---

### aggregate_stats

Aggregate statistics across multiple games.

#### Signature

```python
def aggregate_stats(
    player_id: str,
    game_stats: List[GamePlayerStats]
) -> SeasonStats
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `player_id` | `str` | Yes | Player identifier |
| `game_stats` | `List[GamePlayerStats]` | Yes | Per-game statistics |

#### Returns

`SeasonStats` - Aggregated statistics across all provided games.

#### Example

```python
season = aggregate_stats(
    player_id='player_42',
    game_stats=all_game_stats
)
print(f"Season AVG: {season.batting.batting_average:.3f}")
print(f"Games: {season.games_played}")
```

---

### calculate_team_stats

Calculate team-wide statistics from a game or season.

#### Signature

```python
def calculate_team_stats(
    team: Literal['home', 'away'],
    game_states: List[GameState]
) -> Dict[str, Any]
```

#### Returns

```python
{
    'wins': int,
    'losses': int,
    'runs_scored': int,
    'runs_allowed': int,
    'batting_average': float,
    'era': float,
    'top_hitters': List[Dict],
    'top_pitchers': List[Dict]
}
```

---

## Roster Management Functions

### create_roster

Create a new team roster.

#### Signature

```python
def create_roster(
    team_id: str,
    team_name: str,
    players: List[Player]
) -> Roster
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | `str` | Yes | Unique team identifier |
| `team_name` | `str` | Yes | Display name for team |
| `players` | `List[Player]` | Yes | List of players on roster |

#### Returns

`Roster` - New roster with all players set to ACTIVE status.

#### Example

```python
roster = create_roster(
    team_id='team_1',
    team_name='Tigers',
    players=[
        Player(player_id='p1', name='John Smith', number=42, positions=('1B', 'OF')),
        Player(player_id='p2', name='Mike Johnson', number=17, positions=('P',)),
        # ... more players
    ]
)
```

---

### update_player_status

Update a player's status on the roster.

#### Signature

```python
def update_player_status(
    roster: Roster,
    player_id: str,
    new_status: PlayerStatus
) -> Roster
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `roster` | `Roster` | Yes | Current roster |
| `player_id` | `str` | Yes | Player to update |
| `new_status` | `PlayerStatus` | Yes | New status |

#### Returns

`Roster` - New roster with updated player status.

#### Example

```python
# Move player to injured list
updated_roster = update_player_status(
    roster=roster,
    player_id='p1',
    new_status=PlayerStatus.INJURED
)
```

---

### get_player_game_stats

Get statistics for a specific player in a specific game.

#### Signature

```python
def get_player_game_stats(
    archive: MultiGameArchive,
    player_id: str,
    game_id: str
) -> Optional[GamePlayerStats]
```

#### Returns

`GamePlayerStats` if player participated in game, `None` otherwise.

---

### get_player_season_stats

Get aggregated season statistics for a player.

#### Signature

```python
def get_player_season_stats(
    archive: MultiGameArchive,
    player_id: str
) -> SeasonStats
```

---

## Multi-Game Archive Functions

### create_game_archive

Create a new multi-game archive.

#### Signature

```python
def create_game_archive(
    archive_id: str,
    name: str,
    description: str = ""
) -> MultiGameArchive
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `archive_id` | `str` | Yes | Unique archive identifier |
| `name` | `str` | Yes | Archive name |
| `description` | `str` | No | Archive description |

#### Returns

`MultiGameArchive` - Empty archive ready to receive games.

#### Example

```python
archive = create_game_archive(
    archive_id='season_2024',
    name='2024 Season',
    description='Complete record of 2024 regular season games'
)
```

---

### add_game_to_archive

Add a completed game to an archive.

#### Signature

```python
def add_game_to_archive(
    archive: MultiGameArchive,
    game_state: GameState,
    events: List[Event],
    home_roster: Roster,
    away_roster: Roster,
    metadata: Optional[Dict[str, Any]] = None
) -> MultiGameArchive
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `archive` | `MultiGameArchive` | Yes | Archive to add game to |
| `game_state` | `GameState` | Yes | Final game state |
| `events` | `List[Event]` | Yes | All game events |
| `home_roster` | `Roster` | Yes | Home team roster |
| `away_roster` | `Roster` | Yes | Away team roster |
| `metadata` | `Dict` | No | Additional metadata |

#### Returns

`MultiGameArchive` - Updated archive with new game.

#### Raises

| Exception | Condition |
|-----------|-----------|
| `ValidationError` | Game not in 'final' status |
| `ValidationError` | Duplicate game_id |

#### Example

```python
archive = add_game_to_archive(
    archive=archive,
    game_state=final_state,
    events=all_events,
    home_roster=home_roster,
    away_roster=away_roster,
    metadata={'venue': 'Stadium A', 'attendance': 25000}
)
```

---

### export_archive

Export archive to Baselom JSON format.

#### Signature

```python
def export_archive(
    archive: MultiGameArchive,
    include_events: bool = True,
    include_stats: bool = True
) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `archive` | `MultiGameArchive` | Yes | Archive to export |
| `include_events` | `bool` | No | Include full event history |
| `include_stats` | `bool` | No | Include player statistics |

#### Returns

`Dict[str, Any]` - JSON-serializable dictionary.

#### Example

```python
data = export_archive(archive)
with open('season_2024.baselom.json', 'w') as f:
    json.dump(data, f, indent=2)
```

---

### import_archive

Import archive from Baselom JSON format.

#### Signature

```python
def import_archive(
    data: Dict[str, Any]
) -> MultiGameArchive
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data` | `Dict[str, Any]` | Yes | JSON data to import |

#### Returns

`MultiGameArchive` - Reconstructed archive.

#### Raises

| Exception | Condition |
|-----------|-----------|
| `DeserializationError` | Invalid format |
| `SchemaError` | Version mismatch |

#### Example

```python
with open('season_2024.baselom.json', 'r') as f:
    data = json.load(f)
archive = import_archive(data)
```

---

### query_archive

Query games from archive with filters.

#### Signature

```python
def query_archive(
    archive: MultiGameArchive,
    team_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    player_id: Optional[str] = None
) -> List[GameRecord]
```

#### Example

```python
# Get all games for a specific team in June
games = query_archive(
    archive=archive,
    team_id='team_1',
    start_date='2024-06-01',
    end_date='2024-06-30'
)
```

---

## See Also

- [Data Models](./data-models.md) - Complete model specifications
- [Rules Logic](./rules-logic.md) - Baseball rule processing details
- [Error Handling](./error-handling.md) - Exception hierarchy
- [Serialization](./serialization.md) - Multi-game archive JSON format
