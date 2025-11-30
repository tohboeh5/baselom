# Serialization

## Overview

Baselom Core provides JSON serialization and deserialization for all data models. This enables:

- State persistence and restoration
- Network transmission
- Event logging and replay
- Integration with external systems

## JSON Format Specifications

### GameState JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GameState",
  "type": "object",
  "required": [
    "inning",
    "top",
    "outs",
    "balls",
    "strikes",
    "bases",
    "score",
    "batting_team",
    "fielding_team",
    "lineups",
    "lineup_index",
    "pitchers",
    "game_status",
    "rules_version"
  ],
  "properties": {
    "inning": {
      "type": "integer",
      "minimum": 1,
      "description": "Current inning number (1-based)"
    },
    "top": {
      "type": "boolean",
      "description": "True if top of inning"
    },
    "outs": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2,
      "description": "Current out count"
    },
    "balls": {
      "type": "integer",
      "minimum": 0,
      "maximum": 3,
      "description": "Current ball count"
    },
    "strikes": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2,
      "description": "Current strike count"
    },
    "bases": {
      "type": "array",
      "items": {
        "type": ["string", "null"]
      },
      "minItems": 3,
      "maxItems": 3,
      "description": "Runner IDs on [first, second, third]"
    },
    "score": {
      "type": "object",
      "properties": {
        "home": {"type": "integer", "minimum": 0},
        "away": {"type": "integer", "minimum": 0}
      },
      "required": ["home", "away"]
    },
    "batting_team": {
      "type": "string",
      "enum": ["home", "away"]
    },
    "fielding_team": {
      "type": "string",
      "enum": ["home", "away"]
    },
    "current_pitcher_id": {
      "type": ["string", "null"]
    },
    "current_batter_id": {
      "type": ["string", "null"]
    },
    "lineup_index": {
      "type": "object",
      "properties": {
        "home": {"type": "integer", "minimum": 0, "maximum": 8},
        "away": {"type": "integer", "minimum": 0, "maximum": 8}
      },
      "required": ["home", "away"]
    },
    "lineups": {
      "type": "object",
      "properties": {
        "home": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 9,
          "maxItems": 9
        },
        "away": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 9,
          "maxItems": 9
        }
      },
      "required": ["home", "away"]
    },
    "pitchers": {
      "type": "object",
      "properties": {
        "home": {"type": "string"},
        "away": {"type": "string"}
      },
      "required": ["home", "away"]
    },
    "inning_runs": {
      "type": "object",
      "properties": {
        "home": {"type": "integer", "minimum": 0},
        "away": {"type": "integer", "minimum": 0}
      }
    },
    "game_status": {
      "type": "string",
      "enum": ["in_progress", "final", "suspended", "not_started"]
    },
    "event_history": {
      "type": "array",
      "items": {"type": "object"}
    },
    "rules_version": {
      "type": "string"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### GameRules JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GameRules",
  "type": "object",
  "properties": {
    "designated_hitter": {
      "type": "boolean",
      "default": false
    },
    "max_innings": {
      "type": ["integer", "null"],
      "minimum": 1,
      "default": 9
    },
    "extra_innings_tiebreaker": {
      "type": ["string", "null"],
      "enum": [null, "runner_on_second", "runner_on_first_and_second"]
    },
    "max_extra_innings": {
      "type": ["integer", "null"],
      "minimum": 1
    },
    "mercy_rule_enabled": {
      "type": "boolean",
      "default": false
    },
    "mercy_rule_threshold": {
      "type": "integer",
      "minimum": 1,
      "default": 10
    },
    "mercy_rule_min_inning": {
      "type": "integer",
      "minimum": 1,
      "default": 5
    },
    "allow_balks": {
      "type": "boolean",
      "default": true
    },
    "allow_wild_pitch": {
      "type": "boolean",
      "default": true
    },
    "allow_passed_ball": {
      "type": "boolean",
      "default": true
    },
    "runner_advances_on_error": {
      "type": "boolean",
      "default": true
    },
    "allow_stealing": {
      "type": "boolean",
      "default": true
    },
    "double_switch_allowed": {
      "type": "boolean",
      "default": true
    },
    "reentry_allowed": {
      "type": "boolean",
      "default": false
    },
    "strict_mode": {
      "type": "boolean",
      "default": true
    }
  }
}
```

### Event JSON Schema

#### Base Event Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event",
  "type": "object",
  "required": ["event_type", "event_id", "timestamp", "inning", "top"],
  "properties": {
    "event_type": {
      "type": "string"
    },
    "event_id": {
      "type": "string",
      "format": "uuid"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "inning": {
      "type": "integer",
      "minimum": 1
    },
    "top": {
      "type": "boolean"
    },
    "outs_before": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2
    },
    "outs_after": {
      "type": "integer",
      "minimum": 0,
      "maximum": 3
    }
  }
}
```

#### Hit Event Schema

```json
{
  "allOf": [
    {"$ref": "#/definitions/Event"},
    {
      "type": "object",
      "required": ["batter_id", "pitcher_id", "rbi"],
      "properties": {
        "event_type": {
          "enum": ["single", "double", "triple", "home_run", "ground_rule_double"]
        },
        "batter_id": {"type": "string"},
        "pitcher_id": {"type": "string"},
        "rbi": {"type": "integer", "minimum": 0},
        "runners_scored": {
          "type": "array",
          "items": {"type": "string"}
        },
        "runners_advanced": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "runner_id": {"type": "string"},
              "from_base": {"type": "integer"},
              "to_base": {"type": "integer"}
            }
          }
        }
      }
    }
  ]
}
```

#### Out Event Schema

```json
{
  "allOf": [
    {"$ref": "#/definitions/Event"},
    {
      "type": "object",
      "required": ["batter_id", "pitcher_id"],
      "properties": {
        "event_type": {
          "enum": [
            "strikeout_swinging",
            "strikeout_looking",
            "ground_out",
            "fly_out",
            "line_out",
            "pop_out",
            "double_play",
            "triple_play",
            "force_out",
            "tag_out"
          ]
        },
        "batter_id": {"type": "string"},
        "pitcher_id": {"type": "string"},
        "fielders": {
          "type": "array",
          "items": {"type": "string"}
        },
        "runners_out": {
          "type": "array",
          "items": {"type": "string"}
        },
        "is_sacrifice": {"type": "boolean"}
      }
    }
  ]
}
```

## Serialization Functions

### Python API

```python
from baselom_core import (
    serialize_state,
    deserialize_state,
    serialize_event,
    serialize_rules,
    deserialize_rules
)
import json

# Serialize state to JSON
state_dict = serialize_state(game_state)
state_json = json.dumps(state_dict, indent=2)

# Deserialize state from JSON
state_dict = json.loads(state_json)
game_state = deserialize_state(state_dict)

# Serialize event
event_dict = serialize_event(event)
event_json = json.dumps(event_dict)

# Serialize/deserialize rules
rules_dict = serialize_rules(game_rules)
game_rules = deserialize_rules(rules_dict)
```

### Rust API

```rust
use baselom_core::{GameState, GameRules, Event};
use serde_json;

// Serialize
let state_json = serde_json::to_string(&game_state)?;
let rules_json = serde_json::to_string(&game_rules)?;

// Deserialize
let game_state: GameState = serde_json::from_str(&state_json)?;
let game_rules: GameRules = serde_json::from_str(&rules_json)?;
```

## Example JSON Documents

### Complete GameState Example

```json
{
  "inning": 5,
  "top": false,
  "outs": 1,
  "balls": 2,
  "strikes": 2,
  "bases": ["player_12", null, "player_45"],
  "score": {
    "home": 4,
    "away": 3
  },
  "batting_team": "home",
  "fielding_team": "away",
  "current_pitcher_id": "pitcher_88",
  "current_batter_id": "batter_23",
  "lineup_index": {
    "home": 5,
    "away": 3
  },
  "lineups": {
    "home": ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9"],
    "away": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9"]
  },
  "pitchers": {
    "home": "pitcher_home_1",
    "away": "pitcher_88"
  },
  "inning_runs": {
    "home": 2,
    "away": 0
  },
  "game_status": "in_progress",
  "event_history": [
    {
      "event_type": "single",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T14:30:00Z",
      "inning": 5,
      "top": false,
      "batter_id": "batter_21",
      "pitcher_id": "pitcher_88",
      "rbi": 1
    }
  ],
  "rules_version": "1.0.0",
  "created_at": "2024-01-15T14:35:00Z"
}
```

### Complete GameRules Example

```json
{
  "designated_hitter": true,
  "max_innings": 9,
  "extra_innings_tiebreaker": "runner_on_second",
  "max_extra_innings": null,
  "mercy_rule_enabled": false,
  "mercy_rule_threshold": 10,
  "mercy_rule_min_inning": 5,
  "allow_balks": true,
  "allow_wild_pitch": true,
  "allow_passed_ball": true,
  "runner_advances_on_error": true,
  "allow_stealing": true,
  "double_switch_allowed": true,
  "reentry_allowed": false,
  "strict_mode": true
}
```

### Event Examples

#### Single Event

```json
{
  "event_type": "single",
  "event_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2024-01-15T14:32:15Z",
  "inning": 3,
  "top": true,
  "outs_before": 1,
  "outs_after": 1,
  "batter_id": "batter_05",
  "pitcher_id": "pitcher_22",
  "rbi": 1,
  "runners_scored": ["runner_18"],
  "runners_advanced": [
    {
      "runner_id": "runner_18",
      "from_base": 2,
      "to_base": 4
    },
    {
      "runner_id": "batter_05",
      "from_base": 0,
      "to_base": 1
    }
  ]
}
```

#### Strikeout Event

```json
{
  "event_type": "strikeout_swinging",
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2024-01-15T14:33:45Z",
  "inning": 3,
  "top": true,
  "outs_before": 1,
  "outs_after": 2,
  "batter_id": "batter_06",
  "pitcher_id": "pitcher_22",
  "fielders": [],
  "runners_out": [],
  "is_sacrifice": false,
  "pitch_count": 5,
  "final_count": {
    "balls": 2,
    "strikes": 3
  }
}
```

#### Double Play Event

```json
{
  "event_type": "double_play",
  "event_id": "550e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2024-01-15T14:35:20Z",
  "inning": 4,
  "top": false,
  "outs_before": 0,
  "outs_after": 2,
  "batter_id": "batter_12",
  "pitcher_id": "pitcher_33",
  "fielders": ["ss_44", "2b_55", "1b_66"],
  "runners_out": ["runner_10", "batter_12"],
  "is_sacrifice": false,
  "play_description": "6-4-3 double play"
}
```

#### Substitution Event

```json
{
  "event_type": "substitution",
  "event_id": "550e8400-e29b-41d4-a716-446655440004",
  "timestamp": "2024-01-15T14:40:00Z",
  "inning": 6,
  "top": true,
  "outs_before": 0,
  "outs_after": 0,
  "details": {
    "team": "away",
    "player_out": "pitcher_33",
    "player_in": "pitcher_77",
    "position": "pitcher",
    "batting_order": 8,
    "is_double_switch": false
  }
}
```

## Versioning and Compatibility

### Schema Version

All serialized objects include a `rules_version` field to enable:
- Forward compatibility checks
- Migration between versions
- Validation against appropriate schema

### Version Format

```
MAJOR.MINOR.PATCH

MAJOR: Breaking schema changes
MINOR: New optional fields
PATCH: Bug fixes, documentation
```

### Migration Strategy

```python
def migrate_state(state_dict: dict) -> dict:
    """Migrate state to current schema version."""
    version = state_dict.get('rules_version', '0.0.0')
    
    if version < '1.0.0':
        # Add fields introduced in 1.0.0
        state_dict.setdefault('balls', 0)
        state_dict.setdefault('strikes', 0)
    
    if version < '1.1.0':
        # Add fields introduced in 1.1.0
        state_dict.setdefault('game_status', 'in_progress')
    
    state_dict['rules_version'] = CURRENT_VERSION
    return state_dict
```

## Error Handling

### Deserialization Errors

| Error Type | Cause | Example |
|------------|-------|---------|
| `MissingField` | Required field absent | No `inning` field |
| `InvalidType` | Wrong data type | `outs` is string instead of int |
| `InvalidValue` | Value out of range | `outs` is 5 |
| `InvalidFormat` | Malformed data | Invalid UUID format |

### Error Response Format

```json
{
  "error": "DeserializationError",
  "message": "Invalid value for field 'outs': expected 0-2, got 5",
  "field": "outs",
  "value": 5,
  "expected": "integer in range [0, 2]"
}
```

## Performance Considerations

### Compact Format

For high-frequency serialization, use compact JSON:

```python
# Compact (no whitespace)
json.dumps(state_dict, separators=(',', ':'))

# Result: {"inning":1,"top":true,...}
```

### Binary Format (Future)

For maximum performance, MessagePack support is planned:

```python
# Future API
import msgpack
binary_data = serialize_state_binary(game_state)
game_state = deserialize_state_binary(binary_data)
```

## See Also

- [Data Models](./data-models.md) - Data structure specifications
- [API Reference](./api-reference.md) - Function documentation
- [Error Handling](./error-handling.md) - Error specifications
