# Architecture

## Overview

Baselom Core is a **multi-platform Rust library** that implements a baseball game-state engine as an immutable Finite State Machine (FSM). The core is designed from the ground up to support multiple target platforms:

- **Python** (v0.1.0) - via PyO3/maturin bindings (**Initial Release**)
- **WebAssembly (WASM)** (v0.2.0+) - for browser and edge environments
- **Native** (Linux, macOS, Windows) - via direct Rust compilation
- **Future**: Mobile (iOS/Android), other language bindings

## Release Roadmap

| Version | Platform | Technology | Status |
|---------|----------|------------|--------|
| **v0.1.0** | **Python** | PyO3 + maturin | 🚧 In Development |
| v0.2.0 | WASM | wasm-bindgen | Planned |
| v0.3.0+ | Others | TBD | Future |

> **Architecture Note**: While Python is the initial target, the Rust core is designed without platform-specific dependencies from the start, enabling future WASM and other platform support without architectural changes.

## Multi-Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │   Python    │  │  Browser/   │  │   Native    │  │   Node.js / Edge    ││
│  │ Applications│  │   Web App   │  │   (CLI/GUI) │  │   Runtime           ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘│
└─────────┼────────────────┼────────────────┼───────────────────┼───────────┘
          │                │                │                   │
          ▼                ▼                ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Python Layer   │ │   WASM Module   │ │  Rust FFI    │ │   WASM Module    │
│  (PyO3/maturin) │ │  (wasm-bindgen) │ │  (C ABI)     │ │  (wasm-bindgen)  │
└────────┬────────┘ └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘
         │                   │                 │                  │
         └───────────────────┴────────┬────────┴──────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Rust Core Engine (Platform-Agnostic)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ models.rs   │  │ engine.rs    │  │ validators.rs  │  │ serializer.rs │  │
│  │ (Data Types)│  │ (FSM Logic)  │  │ (State Check)  │  │ (JSON/Binary) │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
│  ┌─────────────┐                                                            │
│  │ errors.rs   │  ← No platform-specific dependencies                       │
│  │ (Error Types)│                                                           │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## WASM-First Design Principles

The architecture follows WASM-compatible design principles to ensure the core library can run in any environment:

### 1. No Standard Library Dependencies (where possible)

```rust
// Core logic uses #![no_std] compatible patterns
// Only alloc crate for heap allocation

#[cfg(not(feature = "std"))]
extern crate alloc;

#[cfg(not(feature = "std"))]
use alloc::{string::String, vec::Vec};
```

### 2. No I/O or System Calls

The core engine performs **no** I/O operations:
- No file system access
- No network calls
- No system time (timestamps provided externally)
- No threading primitives (pure single-threaded logic)

### 3. Serialization-Based Communication

All data exchange uses serializable formats:
- JSON for human-readable interchange
- Binary (MessagePack/bincode) for performance-critical paths
- No raw pointers or platform-specific memory layouts

### 4. Pure Functions

All state transitions are pure functions:
```rust
// Input → Output, no side effects
fn apply_pitch(
    state: &GameState,
    pitch: PitchResult,
    rules: &GameRules
) -> Result<(GameState, Event), BaselomError>
```

## Platform-Specific Bindings

### Python Bindings (PyO3)

```
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
                        [Rust Core Engine]
```

### WASM Bindings (wasm-bindgen) - v0.2.0+

> **Note**: WASM support is planned for v0.2.0.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JavaScript/TypeScript API                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐│
│  │ baselom.d.ts    │  │ baselom.js       │  │ baselom_bg.wasm             ││
│  │ (Type Defs)     │  │ (JS Glue Code)   │  │ (Compiled WASM Binary)      ││
│  └─────────────────┘  └──────────────────┘  └─────────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ wasm-bindgen
                               ▼
                        [Rust Core Engine]
```

### WASM Usage Example (v0.2.0+)

```typescript
// Browser / Node.js
import init, { initialGameState, GameRules, applyPitch } from 'baselom-core';

await init(); // Initialize WASM module

const rules = new GameRules({ designatedHitter: true });
const state = initialGameState(homeLineup, awayLineup, rules);

const [newState, event] = applyPitch(state, 'ball', rules);
console.log(JSON.stringify(event));
```

## System Architecture (Legacy Python-focused view)

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

### Rust Core Dependencies

| Crate | Purpose | WASM Compatible |
|-------|---------|-----------------|
| `serde` | Serialization | ✅ Yes |
| `serde_json` | JSON support | ✅ Yes |
| `thiserror` | Error handling | ✅ Yes |

### Platform-Specific Dependencies

| Crate | Purpose | Platform |
|-------|---------|----------|
| `pyo3` | Python bindings | Native (Python) |
| `wasm-bindgen` | WASM bindings | WebAssembly |
| `js-sys` | JavaScript interop | WebAssembly |
| `web-sys` | Web API access | WebAssembly (Browser) |

### Python Dependencies

| Package | Purpose |
|---------|---------|
| `maturin` | Build tool (dev) |
| `pytest` | Testing (dev) |
| `mypy` | Type checking (dev) |

## Feature Flags

The Rust core supports conditional compilation for different targets:

```toml
# Cargo.toml
[features]
default = ["std"]
std = []           # Enable standard library (native builds)
python = ["pyo3"]  # Enable Python bindings
wasm = ["wasm-bindgen", "js-sys"]  # Enable WASM bindings
```

### Build Configurations

```bash
# Native build (default)
cargo build --release

# Python bindings
maturin build --release

# WASM build
wasm-pack build --target web --release
```

## See Also

- [Data Models](./data-models.md) - Detailed data structure specifications
- [API Reference](./api-reference.md) - Public API documentation
- [Development Guide](./development.md) - Build and setup instructions
