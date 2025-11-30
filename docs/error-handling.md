# Error Handling

## Overview

Baselom Core uses a structured exception hierarchy to provide clear, actionable error information. All errors are designed to be:

- **Specific**: Clear indication of what went wrong
- **Actionable**: Information on how to fix the issue
- **Traceable**: Context for debugging

## Exception Hierarchy

```
BaseBaselomError
├── ValidationError
│   ├── InvalidStateError
│   ├── InvalidInputError
│   └── ConstraintViolationError
├── StateError
│   ├── InvalidTransitionError
│   ├── GameEndedError
│   └── IllegalStateError
├── RuleViolation
│   ├── SubstitutionError
│   ├── LineupError
│   └── PlayError
├── SerializationError
│   ├── DeserializationError
│   └── SchemaError
└── InternalError
```

## Error Classes

### BaseBaselomError

Base class for all Baselom exceptions.

```python
class BaseBaselomError(Exception):
    """Base exception for all Baselom errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error': self.__class__.__name__,
            'code': self.code,
            'message': self.message,
            'details': self.details
        }
```

---

### ValidationError

Raised when input validation fails.

```python
class ValidationError(BaseBaselomError):
    """Input validation failed."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        constraint: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            details={
                'field': field,
                'value': value,
                'constraint': constraint
            }
        )
```

#### Subclasses

| Class | Code | Description |
|-------|------|-------------|
| `InvalidStateError` | `INVALID_STATE` | State object is malformed |
| `InvalidInputError` | `INVALID_INPUT` | Function input is invalid |
| `ConstraintViolationError` | `CONSTRAINT_VIOLATION` | Value violates constraint |

#### Examples

```python
# Invalid lineup size
ValidationError(
    message="Lineup must contain exactly 9 players",
    field="home_lineup",
    value=["p1", "p2", "p3"],  # Only 3 players
    constraint="length == 9"
)

# Invalid outs value
ValidationError(
    message="Outs must be between 0 and 2",
    field="outs",
    value=3,
    constraint="0 <= outs <= 2"
)

# Duplicate player
ValidationError(
    message="Duplicate player in lineup",
    field="away_lineup",
    value="player_1",
    constraint="unique players"
)
```

---

### StateError

Raised when state transition is invalid.

```python
class StateError(BaseBaselomError):
    """State transition error."""
    
    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        attempted_action: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code='STATE_ERROR',
            details={
                'current_state': current_state,
                'attempted_action': attempted_action
            }
        )
```

#### Subclasses

| Class | Code | Description |
|-------|------|-------------|
| `InvalidTransitionError` | `INVALID_TRANSITION` | Transition not allowed |
| `GameEndedError` | `GAME_ENDED` | Game has ended |
| `IllegalStateError` | `ILLEGAL_STATE` | State is inconsistent |

#### Examples

```python
# Game already ended
GameEndedError(
    message="Cannot apply pitch: game has ended",
    current_state="final",
    attempted_action="apply_pitch"
)

# Invalid out count
InvalidTransitionError(
    message="Cannot record out: 3 outs already recorded",
    current_state="outs=3",
    attempted_action="record_out"
)
```

---

### RuleViolation

Raised when baseball rules are violated.

```python
class RuleViolation(BaseBaselomError):
    """Baseball rule violation."""
    
    def __init__(
        self,
        message: str,
        rule: str,
        violation_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code='RULE_VIOLATION',
            details={
                'rule': rule,
                'violation_details': violation_details or {}
            }
        )
```

#### Subclasses

| Class | Code | Description |
|-------|------|-------------|
| `SubstitutionError` | `SUBSTITUTION_ERROR` | Invalid substitution |
| `LineupError` | `LINEUP_ERROR` | Lineup rule violated |
| `PlayError` | `PLAY_ERROR` | Play not allowed |

#### Examples

```python
# Player already in game
SubstitutionError(
    message="Player already in game",
    rule="substitution.unique_player",
    violation_details={
        'player_id': 'player_5',
        'current_position': 'shortstop'
    }
)

# Reentry not allowed
SubstitutionError(
    message="Player reentry not allowed",
    rule="substitution.no_reentry",
    violation_details={
        'player_id': 'player_3',
        'removed_inning': 4
    }
)

# Invalid double switch
SubstitutionError(
    message="Double switch not allowed by rules",
    rule="substitution.double_switch",
    violation_details={
        'double_switch_allowed': False
    }
)
```

---

### SerializationError

Raised when serialization/deserialization fails.

```python
class SerializationError(BaseBaselomError):
    """Serialization or deserialization error."""
    
    def __init__(
        self,
        message: str,
        operation: str,
        source: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code='SERIALIZATION_ERROR',
            details={
                'operation': operation,
                'source': source
            }
        )
```

#### Subclasses

| Class | Code | Description |
|-------|------|-------------|
| `DeserializationError` | `DESERIALIZATION_ERROR` | Cannot parse input |
| `SchemaError` | `SCHEMA_ERROR` | Schema validation failed |

#### Examples

```python
# Missing required field
DeserializationError(
    message="Missing required field: inning",
    operation="deserialize_state",
    source="input_json"
)

# Invalid JSON
DeserializationError(
    message="Invalid JSON syntax at position 45",
    operation="parse_json",
    source="input_string"
)

# Schema violation
SchemaError(
    message="Field 'outs' must be integer, got string",
    operation="validate_schema",
    source="GameState"
)
```

---

### InternalError

Raised for unexpected internal errors.

```python
class InternalError(BaseBaselomError):
    """Unexpected internal error."""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        stack_trace: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code='INTERNAL_ERROR',
            details={
                'component': component,
                'stack_trace': stack_trace
            }
        )
```

## Error Codes Reference

| Code | Category | Description |
|------|----------|-------------|
| `VALIDATION_ERROR` | Validation | General validation failure |
| `INVALID_STATE` | Validation | Invalid state object |
| `INVALID_INPUT` | Validation | Invalid function input |
| `CONSTRAINT_VIOLATION` | Validation | Value constraint violated |
| `STATE_ERROR` | State | General state error |
| `INVALID_TRANSITION` | State | Invalid state transition |
| `GAME_ENDED` | State | Game already ended |
| `ILLEGAL_STATE` | State | Inconsistent state |
| `RULE_VIOLATION` | Rules | General rule violation |
| `SUBSTITUTION_ERROR` | Rules | Invalid substitution |
| `LINEUP_ERROR` | Rules | Lineup rule violated |
| `PLAY_ERROR` | Rules | Play not allowed |
| `SERIALIZATION_ERROR` | Serialization | General serialization error |
| `DESERIALIZATION_ERROR` | Serialization | Cannot deserialize |
| `SCHEMA_ERROR` | Serialization | Schema validation failed |
| `INTERNAL_ERROR` | Internal | Unexpected internal error |

## Error Handling Patterns

### Basic Try-Catch

```python
from baselom_core import apply_pitch, ValidationError, StateError

try:
    new_state, event = apply_pitch(state, 'ball', rules)
except ValidationError as e:
    print(f"Invalid input: {e.message}")
    print(f"Field: {e.details.get('field')}")
except StateError as e:
    print(f"State error: {e.message}")
    print(f"Current state: {e.details.get('current_state')}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Comprehensive Error Handling

```python
from baselom_core import (
    apply_pitch,
    BaseBaselomError,
    ValidationError,
    StateError,
    RuleViolation,
    InternalError
)

def safe_apply_pitch(state, pitch_result, rules):
    """Apply pitch with comprehensive error handling."""
    try:
        return apply_pitch(state, pitch_result, rules)
    
    except ValidationError as e:
        # Log and return helpful message
        logger.warning(f"Validation error: {e.to_dict()}")
        return None, {
            'error': 'Invalid input',
            'details': e.message,
            'field': e.details.get('field')
        }
    
    except StateError as e:
        if e.code == 'GAME_ENDED':
            return None, {'error': 'Game has ended'}
        logger.error(f"State error: {e.to_dict()}")
        return None, {'error': 'Invalid game state'}
    
    except RuleViolation as e:
        return None, {
            'error': 'Rule violation',
            'rule': e.details.get('rule'),
            'message': e.message
        }
    
    except InternalError as e:
        # Log full details, return generic message
        logger.error(f"Internal error: {e.to_dict()}")
        return None, {'error': 'Internal error occurred'}
    
    except Exception as e:
        logger.exception("Unexpected exception")
        raise
```

### Error Recovery

```python
def apply_pitch_with_recovery(state, pitch_result, rules, max_retries=3):
    """Apply pitch with automatic recovery for transient errors."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return apply_pitch(state, pitch_result, rules)
        
        except ValidationError as e:
            # Cannot recover from validation errors
            raise
        
        except InternalError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e.message}")
            continue
    
    # All retries failed
    raise last_error
```

## Rust Error Types

Corresponding Rust error types:

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum BaselomError {
    #[error("Validation error: {message}")]
    Validation {
        message: String,
        field: Option<String>,
        value: Option<String>,
    },
    
    #[error("State error: {message}")]
    State {
        message: String,
        current_state: Option<String>,
        attempted_action: Option<String>,
    },
    
    #[error("Rule violation: {message}")]
    RuleViolation {
        message: String,
        rule: String,
    },
    
    #[error("Serialization error: {message}")]
    Serialization {
        message: String,
        operation: String,
    },
    
    #[error("Internal error: {message}")]
    Internal {
        message: String,
    },
}
```

## Error Propagation (Rust to Python)

Errors in Rust are automatically converted to Python exceptions via PyO3:

```rust
// Rust code
fn apply_pitch_impl(...) -> Result<(GameState, Event), BaselomError> {
    if state.game_status == GameStatus::Final {
        return Err(BaselomError::State {
            message: "Game has ended".to_string(),
            current_state: Some("final".to_string()),
            attempted_action: Some("apply_pitch".to_string()),
        });
    }
    // ...
}

// PyO3 conversion
impl From<BaselomError> for PyErr {
    fn from(err: BaselomError) -> PyErr {
        match err {
            BaselomError::Validation { .. } => {
                ValidationError::new_err(err.to_string())
            }
            BaselomError::State { .. } => {
                StateError::new_err(err.to_string())
            }
            // ...
        }
    }
}
```

## Testing Error Conditions

```python
import pytest
from baselom_core import (
    apply_pitch,
    initial_game_state,
    GameRules,
    ValidationError,
    StateError
)

def test_invalid_lineup_raises_validation_error():
    rules = GameRules()
    with pytest.raises(ValidationError) as exc_info:
        initial_game_state(
            home_lineup=['p1', 'p2'],  # Only 2 players
            away_lineup=['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
            rules=rules
        )
    assert exc_info.value.details['field'] == 'home_lineup'

def test_game_ended_raises_state_error():
    # Setup game in final state
    state = create_finished_game_state()
    rules = GameRules()
    
    with pytest.raises(StateError) as exc_info:
        apply_pitch(state, 'ball', rules)
    
    assert exc_info.value.code == 'GAME_ENDED'
```

## See Also

- [API Reference](./api-reference.md) - Function specifications
- [Testing](./testing.md) - Test strategies including error testing
- [Development Guide](./development.md) - Debugging tips
