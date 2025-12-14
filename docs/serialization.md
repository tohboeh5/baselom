# Serialization

## Overview

Baselom Core provides JSON serialization and deserialization for all data models. This enables:

- State persistence and restoration
- Network transmission
- Event logging and replay
- Integration with external systems

## Design Goals

The serialization system is designed with the following goals:

| Goal | Description |
|------|-------------|
| **Immutability** | Serialized events and state are append-only; once created, they cannot be modified |
| **Semantic Identity** | Two events representing the same play can be compared for equality (excluding timestamps) |
| **Non-redundant History** | History stores events (facts) as diffs, not full state snapshots |
| **Deterministic Serialization** | Same logical value always produces identical byte sequence, enabling hash-based IDs |
| **Version Compatibility** | Schema versions are explicit, with clear migration paths |
| **Cross-platform Support** | Python and Rust produce identical serialized output |

## Canonical JSON Specification

To achieve deterministic serialization, Baselom uses **Canonical JSON** based on [RFC 8785 (JSON Canonicalization Scheme)](https://www.rfc-editor.org/rfc/rfc8785).

### Canonicalization Rules

| Rule | Description |
|------|-------------|
| **Key Ordering** | Object keys are sorted lexicographically (Unicode code point order) |
| **No Whitespace** | No spaces after `:` or `,`; no newlines or indentation |
| **Integer Representation** | Integers are represented without leading zeros or decimal points |
| **Float Representation** | Floats use shortest decimal representation with at least one digit after decimal point |
| **String Encoding** | UTF-8 with minimal escaping (only required escapes: `\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`, `\uXXXX` for control chars) |
| **Null Handling** | `null` fields are included explicitly; missing fields are distinct from `null` |
| **Boolean Representation** | Lowercase `true` and `false` |
| **Enum Representation** | Lowercase string values (e.g., `"single"`, `"strike_called"`) |

### Example

**Non-canonical JSON:**
```json
{
  "strikes": 2,
  "balls": 3,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Canonical JSON:**
```json
{"balls":3,"created_at":"2024-01-15T10:30:00Z","strikes":2}
```

### Implementation Requirements

**Important Note on no_std Environments:**

JSON serialization via `serde_json` requires the standard library (`std` feature). For `no_std` environments (e.g., embedded WASM, resource-constrained targets), use binary serialization formats like `postcard` or `bincode` instead.

See [Architecture - Standard Library Conditional Usage](./architecture.md#1-standard-library-conditional-usage) for complete details on `no_std` builds and serialization strategy.

#### Python

Use `json.dumps()` with specific parameters or a dedicated library:

```python
import json
from typing import Mapping, Any

def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Convert payload to canonical JSON bytes.
    
    Args:
        payload: Data structure to serialize (dict, Mapping, etc.)
    
    Note: For production use, consider using a dedicated RFC 8785 library
    such as `canonicaljson` for full compliance including float handling.
    """
    return json.dumps(
        dict(payload),  # Convert Mapping to dict for json.dumps
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=False
    ).encode('utf-8')
```

#### Rust

Use `serde_json` with deterministic settings:

```rust
use serde::Serialize;
use serde_json::{to_string, Value};

fn canonical_json_bytes<T: Serialize>(payload: &T) -> Vec<u8> {
    // For full RFC 8785 compliance, sort keys during serialization
    let value = serde_json::to_value(payload).unwrap();
    let sorted = sort_keys_recursive(&value);
    serde_json::to_string(&sorted).unwrap().into_bytes()
}
```

---

## Content-Based Event Identification

Events use **content-addressed identification**, where the `event_id` is derived from the event content itself.

### Event ID Generation

```
event_id = SHA-256(schema_version || "|" || event_type || "|" || canonical_json(payload))
```

### Fields Included/Excluded from event_id Calculation

**Fields INCLUDED in event_id:**
- `schema_version`: Event payload schema version (ensures different schemas produce different IDs)
- `event_type`: Type identifier (e.g., `hit.v1`, `out.v1`)
- `payload`: All essential facts for replay:
  - Player IDs (batter, pitcher, runners)
  - Game context (inning, outs_before)
  - Play details (hit_type, out_type)
  - Runner movements (from_base, to_base)
  - Fielder IDs involved
  - Error indicators

**Fields EXCLUDED from event_id:**
- `created_at`: Timestamp varies per event creation
- `actor`: Who/what created the event (e.g., `engine-v0.9`, `scorekeeper-john`)
- `source`: Source system identifier (e.g., `game-server-1`, `mobile-app`)
- `event_id`: The ID itself (obviously)
- Derived values in payload (see below)

**Derived Values NOT Stored in Payload:**

The following values are **computed during replay** and NOT stored in the event payload:
- `rbi`: Runs batted in (calculated from runner movements)
- `runs_scored`: Which runners scored (derived from advances to base 4)
- `score_after`: Game score after event (derived from game state)
- `outs_after`: Out count after event (derived from out_type)

**Rationale:**

This design ensures:
- **Reproducibility**: Same play always generates same `event_id` regardless of when/where created
- **Deduplication**: Identical events detected automatically via matching IDs  
- **Semantic Equality**: Compare events based on game facts, not timestamps or system metadata
- **Integrity Verification**: ID serves as a cryptographic checksum of essential facts
- **Audit Trail**: Timestamps and metadata preserved in envelope without affecting content identity
- **Minimal Storage**: Only essential facts stored; derived values recomputed as needed

### Example

```python
import hashlib
import json

def generate_event_id(payload: dict, event_type: str, schema_version: str) -> str:
    """Generate content-based event ID.
    
    Args:
        payload: Event payload (excluding timestamp and ID)
        event_type: Event type string (e.g., 'pitch_result.v1')
        schema_version: Schema version string (e.g., '1')
    
    Returns:
        SHA-256 hex digest as event ID
    """
    payload_bytes = canonical_json_bytes(payload)
    input_bytes = f"{schema_version}|{event_type}|".encode('utf-8') + payload_bytes
    return hashlib.sha256(input_bytes).hexdigest()
```

---

## Event Envelope/Payload Structure

Events consist of two parts: an **envelope** (metadata) and a **payload** (content).

### Envelope Fields

| Field | Type | In ID Calculation | Description |
|-------|------|-------------------|-------------|
| `event_id` | string | No (derived) | Content-based SHA-256 hash |
| `event_type` | string | Yes | Type identifier (e.g., `pitch_result.v1`) |
| `schema_version` | string | Yes | Schema version for this event type |
| `created_at` | string (ISO 8601) | **No** | Timestamp when event was created |
| `actor` | string | No | Who/what created the event (e.g., `engine-v0.9`) |
| `source` | string | No | Source system identifier |

### Payload Fields

Payload contains only the **essential facts** needed to replay the event. Derived data (like score changes) is NOT included.

### Example Event Structure

```json
{
  "envelope": {
    "event_id": "a1b2c3d4e5f6...",
    "event_type": "pitch_result.v1",
    "schema_version": "1",
    "created_at": "2025-12-01T13:14:15Z",
    "actor": "engine-v0.9",
    "source": "sim-123"
  },
  "payload": {
    "game_id": "game-20251201-xyz",
    "plate_appearance_id": "pa-0001",
    "pitch_number_in_pa": 2,
    "pitch_result": "strike_swinging",
    "batted_ball_result": null,
    "runner_advances": [
      {"from_base": 1, "to_base": 2}
    ]
  }
}
```

---

## State Normalization and Comparison

To compare game states for semantic equality (ignoring timestamps), states must be **normalized** before comparison.

### Normalization Process

1. **Deep copy** the state object
2. **Remove time-like fields**: `created_at`, `updated_at`, `timestamp`, etc.
3. **Canonicalize** the result using the canonical JSON rules above
4. **Hash** the canonical bytes with SHA-256

### Fields Excluded from Normalization

| Field | Reason |
|-------|--------|
| `created_at` | Time of state creation varies |
| `updated_at` | Time of last modification varies |
| `event_history[*].created_at` | Event timestamps vary |
| `event_history[*].event_id` | Derived from content, not semantically relevant for state comparison |

### Implementation

```python
import hashlib
import copy
from typing import Mapping, Any

TIME_FIELDS = {'created_at', 'updated_at', 'timestamp', 'ingested_at'}

def normalize_state(state: Mapping[str, Any]) -> dict:
    """Remove time-like fields from state for comparison.
    
    Args:
        state: State to normalize (accepts dict, Mapping, etc.)
    
    Returns:
        dict with time fields removed recursively
    """
    def remove_time_fields(obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {
                k: remove_time_fields(v) 
                for k, v in obj.items() 
                if k not in TIME_FIELDS
            }
        elif isinstance(obj, (list, tuple)):
            return [remove_time_fields(item) for item in obj]
        else:
            return obj
    
    return remove_time_fields(dict(state))

def state_hash(state: Mapping[str, Any]) -> str:
    """Compute hash of normalized state for comparison.
    
    Args:
        state: State to hash (accepts dict, Mapping, etc.)
    
    Returns:
        SHA-256 hex digest of normalized, canonicalized state
    """
    normalized = normalize_state(state)
    canonical_bytes = canonical_json_bytes(normalized)
    return hashlib.sha256(canonical_bytes).hexdigest()

def states_equal_ignoring_time(
    state1: Mapping[str, Any], 
    state2: Mapping[str, Any]
) -> bool:
    """Check if two states are semantically equal (ignoring timestamps).
    
    Args:
        state1: First state to compare
        state2: Second state to compare
    
    Returns:
        True if states are semantically equal
    """
    return state_hash(state1) == state_hash(state2)
```

### Use Cases

- **Synchronization**: Compare states between distributed systems
- **Replay Verification**: Verify that replaying events produces the same state
- **Testing**: Assert that different code paths produce equivalent results

---

## JSON Format Specifications

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
      "enum": ["in_progress", "final", "suspended"],
      "description": "Current game status. Note: GameStatus enum in data-models.md includes additional states (not_started, postponed, cancelled) for broader use cases, but GameState only uses these three values."
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

Events use an **envelope/payload structure** for clear separation of metadata and content.

#### Event Envelope Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EventEnvelope",
  "type": "object",
  "required": ["event_id", "event_type", "schema_version", "created_at"],
  "properties": {
    "event_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256 hash of (schema_version|event_type|canonical_json(payload))"
    },
    "event_type": {
      "type": "string",
      "description": "Event type identifier with version suffix (e.g., 'pitch_result.v1')"
    },
    "schema_version": {
      "type": "string",
      "description": "Schema version for this event type"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp (UTC with Z suffix). NOT included in event_id calculation."
    },
    "actor": {
      "type": "string",
      "description": "Entity that created this event (e.g., 'engine-v0.9')"
    },
    "source": {
      "type": "string",
      "description": "Source system identifier"
    }
  }
}
```

#### Base Event Payload Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EventPayload",
  "type": "object",
  "required": ["game_id", "inning", "top"],
  "properties": {
    "game_id": {
      "type": "string",
      "description": "Game identifier"
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
    }
  }
}
```

#### Complete Event Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event",
  "type": "object",
  "required": ["envelope", "payload"],
  "properties": {
    "envelope": {"$ref": "#/definitions/EventEnvelope"},
    "payload": {"$ref": "#/definitions/EventPayload"}
  }
}
```

#### Legacy Event Schema (Backward Compatibility)

For backward compatibility, events may also be in **flat format** (without explicit envelope/payload separation). The flat format is deprecated and will be removed in a future major version.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LegacyEvent",
  "type": "object",
  "required": ["event_type", "event_id", "timestamp", "inning", "top"],
  "properties": {
    "event_type": {
      "type": "string"
    },
    "event_id": {
      "type": "string",
      "description": "In legacy format, this may be a UUID instead of content-based hash"
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

#### Hit Event Payload Schema

```json
{
  "allOf": [
    {"$ref": "#/definitions/EventPayload"},
    {
      "type": "object",
      "required": ["batter_id", "pitcher_id", "hit_type"],
      "properties": {
        "hit_type": {
          "enum": ["single", "double", "triple", "home_run", "ground_rule_double"]
        },
        "batter_id": {"type": "string"},
        "pitcher_id": {"type": "string"},
        "runner_advances": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["runner_id", "from_base", "to_base"],
            "properties": {
              "runner_id": {"type": "string"},
              "from_base": {"type": "integer", "minimum": 0, "maximum": 3},
              "to_base": {"type": "integer", "minimum": 1, "maximum": 4}
            }
          },
          "description": "Minimal runner movement info. from_base: 0=batter, 1-3=bases. to_base: 1-3=bases, 4=home."
        }
      }
    }
  ]
}
```

#### Out Event Payload Schema

```json
{
  "allOf": [
    {"$ref": "#/definitions/EventPayload"},
    {
      "type": "object",
      "required": ["batter_id", "pitcher_id", "out_type"],
      "properties": {
        "out_type": {
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
          "items": {"type": "string"},
          "description": "Fielders involved in the out"
        },
        "runners_out": {
          "type": "array",
          "items": {"type": "string"},
          "description": "IDs of runners who were put out"
        },
        "is_sacrifice": {"type": "boolean"}
      }
    }
  ]
}
```

**Note on Derived Fields**: Fields like `rbi` (runs batted in) and `runners_scored` are **not** stored in the payload. They are derived during replay by the engine. This follows the principle that payloads contain only essential facts, not computed values.

### Risks and Mitigation: Replay-Based Derived Information

**Design Decision**: Baselom stores only minimal essential facts in events and derives statistics (RBI, earned runs, etc.) during replay.

**Risks:**

1. **Rule Interpretation Variance**: Different rule versions may compute derived values differently
   - Example: Earned run rules differ between professional-style and youth-focused rule sets
   - Example: Error vs hit scoring judgment affects multiple statistics
   
2. **Replay Consistency**: Replaying old events with new engine versions may produce different statistics

3. **Historical Accuracy**: Rule changes over time mean historical games can't be perfectly replayed

**Mitigation Strategy:**

| Mitigation | Implementation | Purpose |
|------------|----------------|---------|
| **Store Rule Version** | `rules_version` field in GameState | Ensures replay uses correct rule interpretation |
| **Store Essential Context** | Include in payload: `fielders`, `is_error`, `runners_out` | Provides minimal info for consistent replay |
| **Schema Versioning** | `schema_version` in event envelope | Enables payload migration when replay logic changes |
| **Snapshot Strategy** | Periodic state snapshots with derived values | Provides reference points for verification |
| **Audit Fields** | Store `outs_before`, not just `outs_after` | Enables validation of replay correctness |

**Required Minimal Information in Events:**

To ensure consistent replay across rule variations, events MUST include:

- **Who was involved**: Batter ID, pitcher ID, fielder IDs
- **What happened**: Hit type, out type, error indicator
- **Who was out**: `runners_out` list (IDs of players put out)
- **Where runners moved**: Explicit `runner_advances` with from_base/to_base
- **Context**: `outs_before`, `inning`, `top` for state reconstruction

**Example - Ground Out Event:**

```json
{
  "envelope": {
    "event_id": "abc123...",
    "event_type": "out.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "payload": {
    "game_id": "g001",
    "inning": 3,
    "top": true,
    "outs_before": 1,
    "batter_id": "b123",
    "pitcher_id": "p456",
    "out_type": "ground_out",
    "fielders": ["ss_44", "1b_55"],
    "runners_out": ["b123"],
    "is_sacrifice": false,
    "runner_advances": []
  }
}
```

Note: `rbi` is NOT stored. If a runner scores on this out, it's captured in `runner_advances`. The RBI calculation during replay will determine if it counts based on the rule version's interpretation of sacrifice outs vs. productive outs.

**Rule Version Documentation:**

The `rules_version` should follow semantic versioning and include league context:
- `"pro-2024.1.0"` - Professional-style rules, 2024 season, version 1.0
- `"youth-2024.1.0"` - Youth recreational rules, 2024
- `"custom-house-rules-1.0.0"` - Custom rule set

This enables correct replay interpretation when rules differ between leagues or change over time. The version should be incremented when rule interpretations change (e.g., earned run calculation methods, error attribution rules).

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

Note: The `event_history` field may contain full event objects (legacy format) or event references/IDs (optimized format). For scalable deployments, use the [Event History Storage Architecture](#event-history-storage-architecture).

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
      "envelope": {
        "event_id": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
        "event_type": "hit.v1",
        "schema_version": "1",
        "created_at": "2024-01-15T14:30:00Z"
      },
      "payload": {
        "game_id": "game-20240115",
        "inning": 5,
        "top": false,
        "outs_before": 0,
        "batter_id": "batter_21",
        "pitcher_id": "pitcher_88",
        "hit_type": "single",
        "runner_advances": [
          {"runner_id": "batter_21", "from_base": 0, "to_base": 1}
        ]
      }
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

#### Single Event (New Format)

```json
{
  "envelope": {
    "event_id": "a7b3c2d1e4f5678901234567890abcdef1234567890abcdef1234567890abcdef",
    "event_type": "hit.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T14:32:15Z",
    "actor": "baselom-engine-v0.9",
    "source": "game-server-1"
  },
  "payload": {
    "game_id": "game-20240115-001",
    "inning": 3,
    "top": true,
    "outs_before": 1,
    "batter_id": "batter_05",
    "pitcher_id": "pitcher_22",
    "hit_type": "single",
    "runner_advances": [
      {"runner_id": "runner_18", "from_base": 2, "to_base": 4},
      {"runner_id": "batter_05", "from_base": 0, "to_base": 1}
    ]
  }
}
```

**Note**: `rbi` and `runners_scored` are **not** in the payload. They are derived during replay.

#### Strikeout Event (New Format)

```json
{
  "envelope": {
    "event_id": "b8c4d3e2f5a6789012345678901bcdef2345678901bcdef2345678901bcdef01",
    "event_type": "out.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T14:33:45Z",
    "actor": "baselom-engine-v0.9",
    "source": "game-server-1"
  },
  "payload": {
    "game_id": "game-20240115-001",
    "inning": 3,
    "top": true,
    "outs_before": 1,
    "batter_id": "batter_06",
    "pitcher_id": "pitcher_22",
    "out_type": "strikeout_swinging",
    "fielders": [],
    "runners_out": [],
    "is_sacrifice": false
  }
}
```

#### Double Play Event (New Format)

```json
{
  "envelope": {
    "event_id": "c9d5e4f3a6b7890123456789012cdef3456789012cdef3456789012cdef0123",
    "event_type": "out.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T14:35:20Z",
    "actor": "baselom-engine-v0.9",
    "source": "game-server-1"
  },
  "payload": {
    "game_id": "game-20240115-001",
    "inning": 4,
    "top": false,
    "outs_before": 0,
    "batter_id": "batter_12",
    "pitcher_id": "pitcher_33",
    "out_type": "double_play",
    "fielders": ["ss_44", "2b_55", "1b_66"],
    "runners_out": ["runner_10", "batter_12"],
    "is_sacrifice": false
  }
}
```

#### Substitution Event (New Format)

```json
{
  "envelope": {
    "event_id": "d0e6f5a4b7c8901234567890123def4567890123def4567890123def01234567",
    "event_type": "substitution.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T14:40:00Z",
    "actor": "baselom-engine-v0.9",
    "source": "game-server-1"
  },
  "payload": {
    "game_id": "game-20240115-001",
    "inning": 6,
    "top": true,
    "outs_before": 0,
    "team": "away",
    "player_out": "pitcher_33",
    "player_in": "pitcher_77",
    "position": "pitcher",
    "batting_order": 8,
    "is_double_switch": false
  }
}
```

#### Legacy Event Format (Deprecated)

For backward compatibility, the flat format is still supported:

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
    {"runner_id": "runner_18", "from_base": 2, "to_base": 4},
    {"runner_id": "batter_05", "from_base": 0, "to_base": 1}
  ]
}
```

**Deprecation Notice**: The flat format with UUID-based `event_id` is deprecated. New implementations should use the envelope/payload format with content-based IDs.

## Versioning and Compatibility

### Version Types

Baselom uses **three distinct version identifiers**:

| Version Type | Location | Purpose | Included in Hash |
|--------------|----------|---------|------------------|
| `schema_version` | Event envelope | Payload schema version for this event type | **Yes** |
| `rules_version` | GameState | Baseball rules version (e.g., "2024 professional ruleset") | No |
| `baselom_version` | MultiGameArchive | Library version that created the archive | No |

### Event Schema Version

Each event type has its own `schema_version` in the envelope. This is **included in event_id calculation**, ensuring:

- Different schema versions of the same logical event produce different IDs
- Schema migrations don't silently mix incompatible event formats

```json
{
  "envelope": {
    "event_type": "hit.v1",
    "schema_version": "1",  // Included in event_id hash
    ...
  }
}
```

### Version Fields Summary

```json
// In Event
{
  "envelope": {
    "schema_version": "1",      // Event payload schema version
    ...
  }
}

// In GameState
{
  "inning": 5,
  "rules_version": "2024.1.0",  // Baseball rules version
  ...
}

// In MultiGameArchive
{
  "archive_id": "season_2024",
  "baselom_version": "1.2.0",   // Library version
  "games": [...]
}
```

### JSON Schema Version

The JSON schema itself follows semantic versioning:
- **Schema v1.x**: Current stable schema
- Schema changes are documented in CHANGELOG.md

### Version Format

```
MAJOR.MINOR.PATCH

MAJOR: Breaking schema changes (field removal, type changes, required field additions)
MINOR: New optional fields, new enum values
PATCH: Bug fixes, documentation
```

### Compatibility Guarantees

| Scenario | Supported | Notes |
|----------|-----------|-------|
| Read older version data | ✅ Yes | Migration functions apply defaults |
| Read newer MINOR version | ✅ Yes | Unknown fields ignored |
| Read newer MAJOR version | ❌ No | Explicit migration required |
| Write for older version | ⚠️ Limited | May lose new fields |

### Forward Compatibility

When reading data with unknown fields (from a newer minor version):
- Unknown fields are preserved during deserialization
- Unknown enum values raise warnings but don't fail
- Optional fields with unknown defaults use schema defaults

### Backward Compatibility

When reading data from older versions:
- Missing optional fields use schema defaults
- Migration functions handle structural changes
- Required fields missing from old versions cause errors

### Migration Strategy

#### State Migration

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

#### Event Migration

Events with different `schema_version` may need migration. Since `event_id` includes `schema_version`, migrated events will have **new IDs**:

```python
def migrate_event(event_dict: dict, target_schema: str) -> dict:
    """Migrate event payload to target schema version.
    
    Note: This creates a NEW event_id since schema_version changes.
    The original event should be preserved for audit purposes.
    """
    current_schema = event_dict.get('envelope', {}).get('schema_version', '0')
    
    if current_schema == target_schema:
        return event_dict
    
    # Perform migration on payload
    payload = migrate_payload(
        event_dict['payload'],
        event_dict['envelope']['event_type'],
        current_schema,
        target_schema
    )
    
    # Regenerate event_id with new schema
    new_event_id = generate_event_id(
        payload,
        event_dict['envelope']['event_type'],
        target_schema
    )
    
    return {
        'envelope': {
            **event_dict['envelope'],
            'schema_version': target_schema,
            'event_id': new_event_id,
            'migrated_from': event_dict['envelope']['event_id']  # Audit trail
        },
        'payload': payload
    }
```

### Event Type Discriminator

Events use the `event_type` field as a discriminator for polymorphic deserialization. In the new format, `event_type` includes a version suffix:

```python
def deserialize_event(data: dict) -> Event:
    """Deserialize event using type discriminator."""
    # Handle both envelope/payload and flat formats
    if 'envelope' in data:
        event_type = data['envelope']['event_type']
        payload = data['payload']
    else:
        # Legacy flat format
        event_type = data.get('event_type')
        payload = data
    
    # Strip version suffix for type matching
    base_type = event_type.split('.')[0]
    
    if base_type in ('hit', 'single', 'double', 'triple', 'home_run', 'ground_rule_double'):
        return HitEvent(**payload)
    elif base_type in ('out', 'strikeout_swinging', 'strikeout_looking', 'ground_out', ...):
        return OutEvent(**payload)
    elif base_type in ('walk', 'intentional_walk', 'hit_by_pitch'):
        return WalkEvent(**payload)
    else:
        return Event(**payload)  # Base event for unknown types
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

---

## Event History Storage Architecture

For scalable and efficient storage, Baselom recommends separating event storage into three components:

### Storage Components

| Component | Purpose | Key | Value |
|-----------|---------|-----|-------|
| **Events Index** | Track event sequence | `sequence_number` (auto-increment) | `event_id`, `event_type`, `created_at`, `schema_version` |
| **Payload Store** | Store event payloads | `event_id` (content hash) | Canonical JSON bytes (optionally compressed) |
| **Snapshot Store** | Cache game states | `snapshot_id` | `last_sequence_number`, `state_payload_hash`, `created_at` |

### Benefits

1. **Deduplication**: Identical payloads share the same `event_id` key
2. **Immutability**: Append-only index, content-addressed payloads
3. **Fast Replay**: Use snapshots to skip replaying old events
4. **Integrity**: Hash-based IDs enable integrity verification

### Storage Schema (SQL Example)

```sql
-- Events Index: tracks event sequence
CREATE TABLE events_index (
    sequence_number BIGSERIAL PRIMARY KEY,
    event_id CHAR(64) NOT NULL,       -- SHA-256 hex
    event_type VARCHAR(100) NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    UNIQUE(event_id)                   -- Deduplication
);

CREATE INDEX idx_events_game_id ON events_index(game_id);
CREATE INDEX idx_events_created_at ON events_index(created_at);

-- Payload Store: content-addressed event payloads
CREATE TABLE payload_store (
    event_id CHAR(64) PRIMARY KEY,     -- SHA-256 hex
    payload_bytes BYTEA NOT NULL,      -- Canonical JSON (optionally compressed)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshot Store: periodic state snapshots
CREATE TABLE snapshot_store (
    snapshot_id CHAR(64) PRIMARY KEY,  -- SHA-256 of state
    game_id VARCHAR(100) NOT NULL,
    last_sequence_number BIGINT NOT NULL,
    state_bytes BYTEA NOT NULL,        -- Canonical JSON of state
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_snapshots_game_seq ON snapshot_store(game_id, last_sequence_number);
```

### Replay Algorithm

```python
def replay_game(game_id: str, target_sequence: Optional[int] = None) -> GameState:
    """Replay game state from events.
    
    Args:
        game_id: Game identifier
        target_sequence: Replay up to this sequence (None = latest)
    
    Returns:
        Reconstructed GameState
    """
    # 1. Find latest snapshot before target
    snapshot = find_latest_snapshot(game_id, before=target_sequence)
    
    if snapshot:
        state = deserialize_state(snapshot.state_bytes)
        start_sequence = snapshot.last_sequence_number + 1
    else:
        state = initial_game_state(...)
        start_sequence = 1
    
    # 2. Fetch events from snapshot point to target
    events = fetch_events(
        game_id,
        from_sequence=start_sequence,
        to_sequence=target_sequence
    )
    
    # 3. Replay events
    for event_record in events:
        payload = fetch_payload(event_record.event_id)
        state = apply_event(state, payload)
    
    return state
```

### Snapshot Strategy

Create snapshots periodically to optimize replay performance:

- Every N events (e.g., every 100 events)
- At natural boundaries (end of inning, end of game)
- On explicit checkpoint request

```python
def maybe_create_snapshot(state: GameState, sequence_number: int) -> None:
    """Create snapshot if appropriate."""
    SNAPSHOT_INTERVAL = 100
    
    if sequence_number % SNAPSHOT_INTERVAL == 0:
        state_bytes = canonical_json_bytes(serialize_state(state))
        snapshot_id = hashlib.sha256(state_bytes).hexdigest()
        
        save_snapshot(
            snapshot_id=snapshot_id,
            game_id=state.game_id,
            last_sequence_number=sequence_number,
            state_bytes=state_bytes
        )
```

---

## Event History Storage: Tradeoffs and Strategies

The `event_history` field in `GameState` can store event data in multiple ways. The choice affects storage size, replay speed, and data integrity.

### Storage Strategy Options

#### Option 1: Store Event IDs Only (References)

```python
@dataclass(frozen=True)
class GameState:
    # ...
    event_history: Tuple[str, ...]  # Just event_id strings
```

**Pros:**
- ✅ Minimal storage: 64 bytes (SHA-256 hash) per event
- ✅ Deduplication: Identical events share single payload in separate store
- ✅ Immutable: Event IDs never change
- ✅ Fast state serialization: Small JSON size

**Cons:**
- ❌ Requires separate payload store for full event data
- ❌ Slower replay: Must fetch payloads from external store
- ❌ Dependency: State incomplete without payload store access
- ❌ Complex architecture: Needs payload store infrastructure

**Use Cases:**
- Large-scale deployments with many games
- Database-backed systems
- Production environments with separate event storage

**Example:**

```json
{
  "inning": 5,
  "outs": 1,
  "event_history": [
    "a1b2c3d4e5f6...",
    "b2c3d4e5f6a1...",
    "c3d4e5f6a1b2..."
  ]
}
```

#### Option 2: Store Full Event Objects

```python
@dataclass(frozen=True)
class GameState:
    # ...
    event_history: Tuple[Event, ...]  # Complete event objects
```

**Pros:**
- ✅ Self-contained: State includes all event data
- ✅ Fast replay: All data available immediately
- ✅ Simple: No external dependencies
- ✅ Portable: Export/import as single JSON file

**Cons:**
- ❌ Large storage: 200-500 bytes per event (depending on complexity)
- ❌ Redundant data: Duplicate events stored multiple times
- ❌ Slow serialization: Large JSON documents
- ❌ Memory usage: Full event data loaded into memory

**Use Cases:**
- Single-game simulations
- Development and testing
- Small-scale deployments
- Archive exports (self-contained files)

**Example:**

```json
{
  "inning": 5,
  "outs": 1,
  "event_history": [
    {
      "envelope": {
        "event_id": "a1b2c3d4e5f6...",
        "event_type": "hit.v1",
        "schema_version": "1",
        "created_at": "2024-01-15T10:30:00Z"
      },
      "payload": {
        "game_id": "g001",
        "inning": 1,
        "top": true,
        "batter_id": "b123",
        "pitcher_id": "p456",
        "hit_type": "single"
      }
    },
    // ... more complete events
  ]
}
```

#### Option 3: Hybrid - Store Event References with Envelope Metadata

```python
@dataclass(frozen=True) 
class EventReference:
    event_id: str
    event_type: str
    created_at: str  # Quick access without payload lookup

@dataclass(frozen=True)
class GameState:
    # ...
    event_history: Tuple[EventReference, ...]
```

**Pros:**
- ✅ Moderate storage: ~100 bytes per event
- ✅ Quick event type/timestamp access without payload fetch
- ✅ Deduplication: Payloads still shared via event_id
- ✅ Balanced: Good mix of size and accessibility

**Cons:**
- ⚠️ Still requires payload store for full replay
- ⚠️ More complex than pure ID references
- ⚠️ Larger than ID-only approach

**Use Cases:**
- Medium-scale deployments
- When event metadata is frequently accessed
- Systems with caching layers

**Example:**

```json
{
  "inning": 5,
  "outs": 1,
  "event_history": [
    {
      "event_id": "a1b2c3d4e5f6...",
      "event_type": "hit.v1",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "event_id": "b2c3d4e5f6a1...",
      "event_type": "out.v1",
      "created_at": "2024-01-15T10:32:15Z"
    }
  ]
}
```

### Storage Size Comparison

**Typical 9-inning game (~300 events):**

| Strategy | event_history Size | State JSON Size | Replay Time |
|----------|--------------------:|----------------:|------------:|
| **ID Only** | ~19 KB | ~22 KB | ~50ms (with DB) |
| **Full Events** | ~150 KB | ~153 KB | ~5ms (in-memory) |
| **Hybrid** | ~30 KB | ~33 KB | ~30ms (with DB) |

**Calculation Assumptions:**
- **ID Only**: 64 bytes per SHA-256 hash × 300 events = 19,200 bytes
- **Full Events**: ~500 bytes per event (envelope + payload) × 300 = 150,000 bytes
  - Envelope: ~150 bytes (event_id, type, timestamps)
  - Payload: ~350 bytes (game context, player IDs, runner advances)
- **Hybrid**: ~100 bytes per reference (ID + metadata) × 300 = 30,000 bytes
- State base size: ~3 KB (without event_history)
- JSON overhead: ~10-15% (keys, separators, escaping)

*Actual sizes vary based on:*
- Player ID lengths (shorter IDs = smaller payloads)
- Event complexity (double plays, multiple runner advances = larger)
- Compression (gzip can reduce by 60-80%)
- JSON formatting (compact vs pretty-printed)

### Recommendation by Use Case

| Scenario | Recommended Strategy | Rationale |
|----------|---------------------|-----------|
| **Development/Testing** | Full Events | Simplicity, no infrastructure needed |
| **Single Game Simulation** | Full Events | Self-contained, fast replay |
| **Multi-Game Archive Export** | Full Events | Portability, single-file export |
| **Production Database** | ID Only + Separate Payload Store | Deduplication, scalability |
| **Large-Scale Simulation (1000+ games)** | ID Only + Snapshots | Storage efficiency critical |
| **Real-Time Scoring System** | Hybrid | Balance of speed and size |
| **Mobile App** | ID Only | Minimize data transfer |

### Implementation Considerations

#### For ID-Only Storage:

```python
from baselom_core import GameState, Event

def replay_with_payload_store(state: GameState, payload_store) -> GameState:
    """Replay game from event IDs with external payload store.
    
    Args:
        state: Game state with event_history as IDs
        payload_store: Database/cache with event payloads
    
    Returns:
        Reconstructed state with full event data
    """
    events = []
    for event_id in state.event_history:
        payload = payload_store.get(event_id)
        if payload is None:
            raise ValueError(f"Event {event_id} not found in payload store")
        events.append(deserialize_event(payload))
    
    # Replay from initial state
    replay_state = initial_game_state(...)
    for event in events:
        replay_state = apply_event(replay_state, event)
    
    return replay_state
```

#### For Full Event Storage:

```python
def export_self_contained_state(state: GameState) -> dict:
    """Export state with complete event history.
    
    Returns:
        JSON-serializable dict with full events
    """
    return {
        'inning': state.inning,
        'outs': state.outs,
        # ... other fields
        'event_history': [
            serialize_event(event) for event in state.event_history
        ]
    }
```

### Migration Between Strategies

Systems may need to migrate between storage strategies:

```python
def convert_ids_to_full_events(
    state: GameState,
    payload_store
) -> GameState:
    """Convert ID-only event_history to full events.
    
    Useful for: Export, archiving, moving to simpler infrastructure
    """
    full_events = []
    for event_id in state.event_history:
        payload = payload_store.get(event_id)
        envelope = {'event_id': event_id, ...}
        full_events.append({'envelope': envelope, 'payload': payload})
    
    return state._replace(event_history=tuple(full_events))

def convert_full_events_to_ids(
    state: GameState,
    payload_store
) -> GameState:
    """Convert full event_history to IDs only.
    
    Useful for: Database storage, reducing memory usage
    """
    event_ids = []
    for event in state.event_history:
        # Store payload if not already present
        payload_store.put(event['envelope']['event_id'], event['payload'])
        event_ids.append(event['envelope']['event_id'])
    
    return state._replace(event_history=tuple(event_ids))
```

### Performance Optimization: Snapshots

Regardless of strategy, use **snapshots** to avoid replaying entire game history:

```python
# Create snapshot every N events
SNAPSHOT_INTERVAL = 100

if len(state.event_history) % SNAPSHOT_INTERVAL == 0:
    snapshot_store.save(state.game_id, state)

# Replay from nearest snapshot
def fast_replay(game_id: str, target_event: int):
    # Get nearest snapshot before target
    snapshot = snapshot_store.get_before(game_id, target_event)
    
    # Replay only events since snapshot
    remaining_events = fetch_events(
        game_id,
        from_seq=snapshot.last_event_seq,
        to_seq=target_event
    )
    
    state = snapshot.state
    for event in remaining_events:
        state = apply_event(state, event)
    
    return state
```

See [Event History Storage Architecture](#event-history-storage-architecture) for database schema and implementation details.

---

## Multi-Game Archive Format

Baselom provides a native JSON format for storing multiple games with full metadata, statistics, and event history.

### Archive JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MultiGameArchive",
  "type": "object",
  "required": ["archive_id", "name", "games", "baselom_version"],
  "properties": {
    "archive_id": {
      "type": "string",
      "description": "Unique archive identifier"
    },
    "name": {
      "type": "string",
      "description": "Archive name"
    },
    "description": {
      "type": "string",
      "description": "Archive description"
    },
    "games": {
      "type": "array",
      "items": {"$ref": "#/definitions/GameRecord"}
    },
    "rosters": {
      "type": "object",
      "additionalProperties": {"$ref": "#/definitions/Roster"}
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    },
    "baselom_version": {
      "type": "string",
      "description": "Baselom version used to create archive"
    }
  }
}
```

### GameRecord JSON Schema

```json
{
  "title": "GameRecord",
  "type": "object",
  "required": ["game_id", "date", "home_team", "away_team", "final_state"],
  "properties": {
    "game_id": {"type": "string"},
    "date": {"type": "string", "format": "date"},
    "home_team": {"type": "string"},
    "away_team": {"type": "string"},
    "final_state": {"$ref": "#/definitions/GameState"},
    "events": {
      "type": "array",
      "items": {"$ref": "#/definitions/Event"}
    },
    "player_stats": {
      "type": "array",
      "items": {"$ref": "#/definitions/GamePlayerStats"}
    },
    "substitutions": {
      "type": "array",
      "items": {"$ref": "#/definitions/SubstitutionRecord"}
    },
    "rules": {"$ref": "#/definitions/GameRules"},
    "metadata": {
      "type": "object",
      "properties": {
        "venue": {"type": "string"},
        "attendance": {"type": "integer"},
        "weather": {"type": "string"},
        "duration_minutes": {"type": "integer"},
        "umpires": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

### Player Statistics JSON Schema

```json
{
  "title": "GamePlayerStats",
  "type": "object",
  "required": ["player_id", "game_id", "team"],
  "properties": {
    "player_id": {"type": "string"},
    "game_id": {"type": "string"},
    "team": {"enum": ["home", "away"]},
    "started": {"type": "boolean"},
    "entered_game": {"type": "boolean"},
    "batting_order": {"type": ["integer", "null"]},
    "batting": {
      "type": "object",
      "properties": {
        "plate_appearances": {"type": "integer"},
        "at_bats": {"type": "integer"},
        "hits": {"type": "integer"},
        "singles": {"type": "integer"},
        "doubles": {"type": "integer"},
        "triples": {"type": "integer"},
        "home_runs": {"type": "integer"},
        "runs": {"type": "integer"},
        "rbi": {"type": "integer"},
        "walks": {"type": "integer"},
        "strikeouts": {"type": "integer"},
        "hit_by_pitch": {"type": "integer"}
      }
    },
    "pitching": {
      "type": ["object", "null"],
      "properties": {
        "innings_pitched": {"type": "number"},
        "hits_allowed": {"type": "integer"},
        "runs_allowed": {"type": "integer"},
        "earned_runs": {"type": "integer"},
        "walks_allowed": {"type": "integer"},
        "strikeouts": {"type": "integer"},
        "home_runs_allowed": {"type": "integer"},
        "pitches_thrown": {"type": "integer"},
        "win": {"type": "boolean"},
        "loss": {"type": "boolean"},
        "save": {"type": "boolean"}
      }
    }
  }
}
```

### Roster JSON Schema

```json
{
  "title": "Roster",
  "type": "object",
  "required": ["team_id", "team_name", "players"],
  "properties": {
    "team_id": {"type": "string"},
    "team_name": {"type": "string"},
    "players": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["player_id", "name"],
        "properties": {
          "player_id": {"type": "string"},
          "name": {"type": "string"},
          "number": {"type": ["integer", "null"]},
          "positions": {
            "type": "array",
            "items": {"type": "string"}
          },
          "bats": {"enum": ["L", "R", "S"]},
          "throws": {"enum": ["L", "R"]},
          "status": {
            "enum": ["active", "bench", "injured", "inactive"]
          }
        }
      }
    }
  }
}
```

### Complete Archive Example

```json
{
  "archive_id": "season_2024",
  "name": "2024 Regular Season",
  "description": "Complete record of 2024 regular season games",
  "baselom_version": "1.0.0",
  "created_at": "2024-04-01T00:00:00Z",
  "updated_at": "2024-10-01T23:59:59Z",
  "rosters": {
    "tigers": {
      "team_id": "tigers",
      "team_name": "Tigers",
      "players": [
        {
          "player_id": "smith_42",
          "name": "John Smith",
          "number": 42,
          "positions": ["1B", "OF"],
          "bats": "R",
          "throws": "R",
          "status": "active"
        },
        {
          "player_id": "johnson_17",
          "name": "Mike Johnson",
          "number": 17,
          "positions": ["P"],
          "bats": "L",
          "throws": "L",
          "status": "active"
        }
      ]
    },
    "eagles": {
      "team_id": "eagles",
      "team_name": "Eagles",
      "players": []
    }
  },
  "games": [
    {
      "game_id": "game_001",
      "date": "2024-04-01",
      "home_team": "tigers",
      "away_team": "eagles",
      "final_state": {
        "inning": 9,
        "top": true,
        "outs": 3,
        "score": {"home": 5, "away": 3},
        "game_status": "final"
      },
      "events": [],
      "player_stats": [
        {
          "player_id": "smith_42",
          "game_id": "game_001",
          "team": "home",
          "started": true,
          "batting_order": 3,
          "batting": {
            "plate_appearances": 4,
            "at_bats": 4,
            "hits": 2,
            "singles": 1,
            "doubles": 1,
            "triples": 0,
            "home_runs": 0,
            "runs": 1,
            "rbi": 2,
            "walks": 0,
            "strikeouts": 1
          }
        }
      ],
      "substitutions": [
        {
          "game_id": "game_001",
          "inning": 7,
          "top": true,
          "team": "home",
          "player_out_id": "starter_p",
          "player_in_id": "reliever_1",
          "position": "P",
          "batting_order": 8,
          "timestamp": "2024-04-01T21:30:00Z"
        }
      ],
      "rules": {
        "designated_hitter": true,
        "max_innings": 9
      },
      "metadata": {
        "venue": "Tiger Stadium",
        "attendance": 35000,
        "weather": "Clear, 72°F",
        "duration_minutes": 175
      }
    }
  ]
}
```

### Archive File Naming Convention

Baselom archives use the `.baselom.json` extension:

```
season_2024.baselom.json
tournament_summer.baselom.json
team_tigers_games.baselom.json
```

### Serialization Functions

```python
from baselom_core import (
    export_archive,
    import_archive,
    validate_archive
)
import json

# Export archive to JSON
archive_data = export_archive(archive)
with open('season.baselom.json', 'w') as f:
    json.dump(archive_data, f, indent=2)

# Import archive from JSON
with open('season.baselom.json', 'r') as f:
    archive_data = json.load(f)
archive = import_archive(archive_data)

# Validate archive before import
validation_result = validate_archive(archive_data)
if not validation_result.is_valid:
    print(f"Errors: {validation_result.errors}")
```

## See Also

- [Data Models](./data-models.md) - Data structure specifications
- [API Reference](./api-reference.md) - Function documentation
- [Error Handling](./error-handling.md) - Error specifications
