# Rules Logic

## Overview

This document specifies the baseball rules logic implemented in Baselom Core. All rules are configurable through `GameRules` and implemented as deterministic state transitions.

## Game Flow

### Game Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         GAME                                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    INNING 1                          │    │
│  │  ┌──────────────┐    ┌──────────────┐               │    │
│  │  │  Top (Away)  │ → │ Bottom (Home)│               │    │
│  │  │  3 outs      │    │  3 outs      │               │    │
│  │  └──────────────┘    └──────────────┘               │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    INNING 2                          │    │
│  │              (repeat structure)                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ...                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    INNING 9+                         │    │
│  │         (until winner determined)                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Half-Inning Flow

```
START HALF-INNING
       │
       ▼
┌──────────────────┐
│  Set batter to   │
│  next in lineup  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   PLATE          │ ◄──────────────────────────┐
│  APPEARANCE      │                             │
└────────┬─────────┘                             │
         │                                       │
    ┌────┴────┐                                  │
    │ Pitch   │                                  │
    │ Result  │                                  │
    └────┬────┘                                  │
         │                                       │
    ┌────┴────────────────────────────┐          │
    │                                  │          │
    ▼                                  ▼          │
 [Walk/HBP]                      [Strikeout]      │
    │                                  │          │
    │                              +1 out         │
    │                                  │          │
    │    ┌─────────────────────────────┤          │
    │    │                             │          │
    ▼    ▼                             ▼          │
 [Hit/In Play]                   outs < 3 ?      │
    │                                  │          │
    │                             Yes  │  No      │
    │                              │   │          │
    │                              │   ▼          │
    │                              │  END         │
    │                              │  HALF        │
    ▼                              │  INNING      │
 Process                           │              │
 runners                           │              │
    │                              │              │
    └──────────────────────────────┴──────────────┘
                    │
                    │ Next batter
                    │
                    └─────────────────────────────►
```

## Count Processing

### Ball-Strike Count

| Situation | Action |
|-----------|--------|
| Ball (count < 3 balls) | Increment ball count |
| Ball (count = 3 balls) | Walk (batter to 1st) |
| Strike (count < 2 strikes) | Increment strike count |
| Strike (count = 2 strikes, not foul) | Strikeout |
| Foul (count < 2 strikes) | Increment strike count |
| Foul (count = 2 strikes) | No change (except foul tip) |
| Foul tip (2 strikes) | Strikeout (if caught) |

### Count Transition Table

```
Current      Pitch Result    New Count      Special Action
─────────────────────────────────────────────────────────────
0-0          Ball            1-0            -
0-0          Strike          0-1            -
0-0          Foul            0-1            -
...
3-0          Ball            -              Walk
3-0          Strike          3-1            -
3-2          Ball            -              Walk
3-2          Strike (swing)  -              Strikeout
3-2          Foul            3-2            No change
3-2          Foul tip (out)  -              Strikeout
```

## Hit Processing

### Hit Types and Base Assignment

| Hit Type | Batter Position | Default Runner Movement |
|----------|-----------------|------------------------|
| Single | 1st base | Runners advance 1-2 bases |
| Double | 2nd base | Runners advance 2-3 bases |
| Triple | 3rd base | All runners score |
| Home Run | Score | All runners score |
| Ground Rule Double | 2nd base | Runners advance 2 bases |

### Runner Advancement Rules

#### On Single

```
Runner on:    Advances to:
─────────────────────────
3rd base  →   Home (scores)
2nd base  →   Home (scores) or 3rd
1st base  →   2nd or 3rd
Batter    →   1st base
```

#### On Double

```
Runner on:    Advances to:
─────────────────────────
3rd base  →   Home (scores)
2nd base  →   Home (scores)
1st base  →   3rd or Home
Batter    →   2nd base
```

#### On Triple

```
Runner on:    Advances to:
─────────────────────────
3rd base  →   Home (scores)
2nd base  →   Home (scores)
1st base  →   Home (scores)
Batter    →   3rd base
```

#### On Home Run

```
All runners score
Batter scores
```

## Out Processing

### Out Types

| Out Type | Description | Outs Added |
|----------|-------------|------------|
| Strikeout | 3 strikes | 1 |
| Ground out | Ball fielded, thrown to 1st | 1 |
| Fly out | Ball caught in air | 1 |
| Line out | Line drive caught | 1 |
| Pop out | Pop fly caught | 1 |
| Force out | Runner forced at base | 1 |
| Tag out | Runner tagged | 1 |
| Double play | 2 outs on one play | 2 |
| Triple play | 3 outs on one play | 3 |

### Force Play Rules

A force play exists when:
- Runner must advance because batter becomes runner
- All bases behind the runner are occupied

```
Bases: [Runner1, Runner2, Runner3] = (1st, 2nd, 3rd)

Scenario: Bases loaded, ground ball
  - Force at home (3rd → Home)
  - Force at 3rd (2nd → 3rd)
  - Force at 2nd (1st → 2nd)
  - Force at 1st (Batter → 1st)

Scenario: Runner on 2nd only, ground ball
  - Only force at 1st (Batter → 1st)
  - Runner on 2nd NOT forced
```

### Double Play Scenarios

| Scenario | Type | Outs |
|----------|------|------|
| Ground ball, 6-4-3 | Force double play | 2 |
| Line drive, runner off base | Unassisted double play | 2 |
| Strikeout + caught stealing | Strikeout double play | 2 |
| Fly out, runner tags early | Tag double play | 2 |

### Sacrifice Rules

| Type | Condition | Batter Statistics |
|------|-----------|-------------------|
| Sacrifice Fly | Fly out scores runner from 3rd | No AB charged |
| Sacrifice Bunt | Bunt out advances runner | No AB charged |

## Walk and Hit By Pitch

### Walk Processing

```python
def process_walk(state, rules):
    """
    Process walk - batter awarded first base, forced runners advance.
    
    Note: This is pseudocode showing the logic flow.
    Actual implementation creates new immutable state.
    """
    # Extract current base state (immutable tuple)
    first, second, third = state.bases
    runs_scored = 0
    
    # Check for forced advances
    if first is not None:  # Runner on 1st
        if second is not None:  # Runner on 2nd
            if third is not None:  # Runner on 3rd
                runs_scored += 1  # Runner scores
                new_third = second  # 2nd → 3rd
            else:
                new_third = second
            new_second = first  # 1st → 2nd
        else:
            new_second = first
            new_third = third
        new_first = state.current_batter_id  # Batter → 1st
    else:
        new_first = state.current_batter_id
        new_second = second
        new_third = third
    
    # Return new immutable tuple
    new_bases = (new_first, new_second, new_third)
    return new_bases, runs_scored
```

### Hit By Pitch

Same as walk, but different event type.

## Base Running Rules

### Stolen Base

Requirements:
- Runner on base
- Ball not in play
- `allow_stealing` rule enabled

Processing:
1. Runner attempts to advance
2. If successful: Runner moves to next base
3. If unsuccessful: Runner out (caught stealing)

### Wild Pitch / Passed Ball

When wild pitch or passed ball occurs:
1. All runners may advance one base
2. Runner on 3rd may score

### Balk

When balk is called:
1. All runners advance one base
2. If bases empty, ball is awarded to batter

### Tag Up Rule

On fly out:
1. Runners must return to or stay on their base
2. After catch, runners may advance
3. If runner leaves early, appeal can result in out

## Inning Transitions

### End of Half-Inning

Triggered when:
- 3 outs recorded
- Explicit `end_half_inning()` call (special cases)

Processing:
```python
def end_half_inning(state, rules):
    # Clear bases
    new_bases = (None, None, None)
    
    # Reset outs
    new_outs = 0
    
    # Reset count
    new_balls = 0
    new_strikes = 0
    
    # Swap teams
    if state.top:
        new_top = False
        new_inning = state.inning
    else:
        new_top = True
        new_inning = state.inning + 1
    
    return new_state
```

### Extra Innings

When game is tied after regulation:

| Rule Setting | Behavior |
|--------------|----------|
| `extra_innings_tiebreaker = None` | Normal rules continue |
| `extra_innings_tiebreaker = 'runner_on_second'` | Each half starts with runner on 2nd |
| `extra_innings_tiebreaker = 'runner_on_first_and_second'` | Each half starts with runners on 1st and 2nd |

### Tiebreaker Runner Placement

```python
def setup_extra_inning(state, rules):
    if rules.extra_innings_tiebreaker == 'runner_on_second':
        # Place runner (last batter of previous inning)
        runner_id = get_last_out_batter(state)
        new_bases = (None, runner_id, None)
    elif rules.extra_innings_tiebreaker == 'runner_on_first_and_second':
        runner1 = get_last_out_batter(state, offset=0)
        runner2 = get_last_out_batter(state, offset=1)
        new_bases = (runner1, runner2, None)
    else:
        new_bases = (None, None, None)
    
    return new_bases
```

## Game End Conditions

### Win Conditions

| Condition | Winner |
|-----------|--------|
| End of 9th, visitor ahead | Visitor |
| End of 9th, home ahead | Home |
| Bottom 9th+, home takes lead | Home (walk-off) |
| Mercy rule triggered | Team with lead |

### Walk-Off Logic

```python
def check_walkoff(state, rules):
    if state.inning >= rules.max_innings and not state.top:
        # Bottom of 9th or later
        if state.score['home'] > state.score['away']:
            return True, 'home'
    return False, None
```

### Mercy Rule

```python
def check_mercy_rule(state, rules):
    if not rules.mercy_rule_enabled:
        return False, None
    
    if state.inning < rules.mercy_rule_min_inning:
        return False, None
    
    diff = abs(state.score['home'] - state.score['away'])
    if diff >= rules.mercy_rule_threshold:
        winner = 'home' if state.score['home'] > state.score['away'] else 'away'
        return True, winner
    
    return False, None
```

## Designated Hitter Rules

### DH Configuration

When `designated_hitter = True`:
- 10 players in lineup (9 fielding + DH)
- DH bats in place of pitcher
- Pitcher does not bat

### DH Loss Conditions

DH is lost if:
1. DH enters as fielder
2. Pitcher enters batting order
3. DH moves to field position

```python
def check_dh_lost(state, substitution):
    if substitution.player_in == state.pitchers[substitution.team]:
        # Pitcher entering batting order
        return True
    if is_dh(state, substitution.player_out) and is_field_position(substitution.new_position):
        # DH moving to field
        return True
    return False
```

## Substitution Rules

### Basic Substitution

1. New player enters game
2. Replaced player cannot return (unless `reentry_allowed`)
3. New player inherits batting order position

### Double Switch

When `double_switch_allowed = True`:
1. Two simultaneous substitutions
2. Players enter at different batting order positions
3. Used to avoid pitcher batting soon

```python
def validate_double_switch(request, state, rules):
    if not rules.double_switch_allowed:
        raise RuleViolation("Double switch not allowed")
    
    # Verify two substitutions
    if request.double_switch_partner is None:
        raise RuleViolation("Double switch requires partner")
    
    # Verify different positions
    if request.position == request.double_switch_partner.position:
        raise RuleViolation("Double switch must use different positions")
```

### Pitcher Substitution

Special rules for pitchers:
1. Must face minimum batters (or complete inning) in some rules
2. Relief pitcher may enter mid-at-bat
3. Pitcher injury exception may apply

## RBI Calculation

### RBI Credited

| Situation | RBI Credited |
|-----------|--------------|
| Hit scores runner | Yes |
| Walk with bases loaded | Yes |
| Hit by pitch with bases loaded | Yes |
| Sacrifice fly | Yes |
| Sacrifice bunt | Yes |
| Groundout scores runner | Yes (if not double play) |

### RBI Not Credited

| Situation | RBI Credited |
|-----------|--------------|
| Error allows run | No |
| Double play scores run | No |
| Wild pitch scores run | No |
| Passed ball scores run | No |
| Balk scores run | No |

```python
def calculate_rbi(play_result, runners_scored):
    if play_result.is_error:
        return 0
    if play_result.is_double_play and runners_scored > 0:
        # Only first run on DP doesn't count
        return max(0, runners_scored - 1)
    return runners_scored
```

## See Also

- [Data Models](./data-models.md) - State and event structures
- [API Reference](./api-reference.md) - Function specifications
- [Testing](./testing.md) - Rule verification tests
