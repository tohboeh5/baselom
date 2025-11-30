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
| `runner_advances` | `Dict[int, int]` | No | Manual runner advancement {from_base: to_base} |

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

## See Also

- [Data Models](./data-models.md) - Complete model specifications
- [Rules Logic](./rules-logic.md) - Baseball rule processing details
- [Error Handling](./error-handling.md) - Exception hierarchy
