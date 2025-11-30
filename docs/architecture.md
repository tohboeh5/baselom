# Architecture

## Overview

Baselom Core is a Rust/Python hybrid library that implements a baseball game-state engine as an immutable Finite State Machine (FSM).

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
│              (Baseball Simulators, Game Management Systems)                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python API Layer                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ models.py   │  │ engine.py    │  │ validators.py  │  │ serializer.py │  │
│  │ (Type Hints)│  │ (Wrappers)   │  │ (Validation)   │  │ (JSON I/O)    │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
│  ┌─────────────┐                                                            │
│  │exceptions.py│                                                            │
│  │ (Errors)    │                                                            │
│  └─────────────┘                                                            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ PyO3 FFI Bindings
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Rust Core Engine                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐                      │
│  │ models.rs   │  │ engine.rs    │  │ validators.rs  │                      │
│  │ (Data Types)│  │ (FSM Logic)  │  │ (State Check)  │                      │
│  └─────────────┘  └──────────────┘  └────────────────┘                      │
│  ┌─────────────┐  ┌──────────────┐                                          │
│  │ errors.rs   │  │ lib.rs       │                                          │
│  │ (Error Types)│ │ (Entry Point)│                                          │
│  └─────────────┘  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Single Responsibility

Baselom Core is **only** responsible for:

- Rule compliance checking
- State transitions
- Event generation

It does **not** handle:

- Player abilities or statistics
- Randomness or probability
- Game strategy or AI
- User interface
- Network communication
- Data persistence

### 2. Immutability

All state objects are immutable:

```python
# Every state transition creates a new instance
new_state, event = apply_pitch(old_state, pitch_result, rules)

# old_state remains unchanged
assert old_state.outs == 0
assert new_state.outs == 1  # New state reflects the change
```

Benefits:
- **Thread Safety**: No race conditions
- **Debuggability**: Complete state history available
- **Testability**: Predictable, reproducible behavior
- **Replay**: Easy to reconstruct game from events

### 3. Finite State Machine (FSM)

The game engine operates as a pure FSM:

```
┌─────────────────────────────────────────────────────────────────┐
│                          FSM States                              │
├─────────────────────────────────────────────────────────────────┤
│  AWAITING_PITCH        → Waiting for next pitch/play            │
│  AWAITING_RUNNER_ACTION → Runner decision needed                │
│  HALF_INNING_END       → Transitioning between half-innings     │
│  GAME_END              → Final state (winner determined)        │
└─────────────────────────────────────────────────────────────────┘

Transitions:
  (State, Input) → (NewState, Event)
```

### 4. Event Sourcing

Every state change produces an event:

```json
{
  "type": "single",
  "timestamp": "2024-01-15T10:30:00Z",
  "inning": 3,
  "top": true,
  "batter": "player_123",
  "pitcher": "player_456",
  "runners_advanced": [
    {"runner": "player_789", "from": 1, "to": 3}
  ],
  "rbi": 0
}
```

Events enable:
- Full game replay
- Analytics and statistics
- Undo/redo functionality
- External system integration

## Component Details

### Rust Core (`src/`)

| File | Responsibility |
|------|----------------|
| `lib.rs` | PyO3 module entry point, exports |
| `models.rs` | Core data structures |
| `engine.rs` | FSM transition logic |
| `validators.rs` | State validation rules |
| `errors.rs` | Error type definitions |

### Python Layer (`baselom_core/`)

| File | Responsibility |
|------|----------------|
| `__init__.py` | Package exports |
| `models.py` | Python dataclass definitions, type hints |
| `engine.py` | Wrapper functions around Rust core |
| `validators.py` | Additional Python-side validation |
| `serializer.py` | JSON serialization/deserialization |
| `exceptions.py` | Python exception hierarchy |

## Data Flow

### Pitch Processing Flow

```
1. Client calls apply_pitch(state, pitch_result, rules)
           │
           ▼
2. Python layer validates input parameters
           │
           ▼
3. Rust core processes state transition
   ├─ Validate current state
   ├─ Apply baseball rules
   ├─ Calculate new state
   └─ Generate event
           │
           ▼
4. Python layer converts to Python objects
           │
           ▼
5. Return (new_state, event) to client
```

### State Validation Flow

```
1. validate_state(state) called
           │
           ▼
2. Rust validators check:
   ├─ Outs in valid range (0-2)
   ├─ Inning number valid
   ├─ Base runners valid
   ├─ Score consistency
   └─ Lineup consistency
           │
           ▼
3. Return ValidationResult with any errors
```

## Performance Considerations

### Rust Core Benefits

- **Zero-cost abstractions**: No runtime overhead
- **Memory safety**: No garbage collection pauses
- **Native performance**: Compiled to machine code

### Python Bindings

- **PyO3/maturin**: Efficient FFI with minimal overhead
- **Type coercion**: Automatic conversion between Rust/Python types
- **GIL management**: Release GIL during Rust computations

### Benchmarks (Target)

| Operation | Target Latency |
|-----------|----------------|
| `apply_pitch()` | < 100μs |
| `validate_state()` | < 50μs |
| State serialization | < 100μs |
| Full game simulation (9 innings, ~300 pitches) | < 50ms |

*Note: These are initial targets. Actual benchmarks will be measured and documented after implementation.*

## Thread Safety

### Guarantees

- All state objects are **immutable** → inherently thread-safe
- Pure functions → no side effects
- No global mutable state

### Usage Pattern

```python
import concurrent.futures
from baselom_core import apply_pitch

def simulate_game(initial_state, plays):
    state = initial_state
    events = []
    for play in plays:
        state, event = apply_pitch(state, play, rules)
        events.append(event)
    return events

# Safe to run multiple simulations in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(simulate_game, state, plays)
        for state, plays in game_scenarios
    ]
    results = [f.result() for f in futures]
```

## Error Handling Strategy

### Error Categories

| Category | Description | Example |
|----------|-------------|---------|
| `ValidationError` | Invalid input data | Negative inning number |
| `StateError` | Invalid state transition | 4 outs attempted |
| `RuleViolation` | Rule constraint violated | Invalid substitution |
| `InternalError` | Unexpected system error | Memory allocation failure |

### Error Propagation

```
Rust Error → PyO3 Exception → Python Exception
             (Automatic)      (Custom mapping)
```

## Extension Points

### Custom Rules

```python
rules = GameRules(
    designated_hitter=True,
    max_innings=7,  # Minor league rules
    extra_innings_tiebreaker="runner_on_second",
    mercy_rule_threshold=10
)
```

### Custom Events

The event system can be extended to include:
- Custom event types
- Additional metadata
- External system hooks

## Dependencies

### Rust Dependencies

| Crate | Purpose |
|-------|---------|
| `pyo3` | Python bindings |
| `serde` | Serialization |
| `serde_json` | JSON support |
| `thiserror` | Error handling |

### Python Dependencies

| Package | Purpose |
|---------|---------|
| `maturin` | Build tool (dev) |
| `pytest` | Testing (dev) |
| `mypy` | Type checking (dev) |

## See Also

- [Data Models](./data-models.md) - Detailed data structure specifications
- [API Reference](./api-reference.md) - Public API documentation
- [Development Guide](./development.md) - Build and setup instructions
