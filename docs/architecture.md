# Architecture

## Overview

Baselom Core is a **multi-platform Rust library** that implements a baseball game-state engine as an immutable Finite State Machine (FSM). The core is designed for both **game simulations** and **real-world game management**, supporting multiple target platforms:

- **Python** (v0.1.0) - via PyO3/maturin bindings (**Initial Release**)
- **WebAssembly (WASM)** (v0.2.0+) - for browser and edge environments
- **Native** (Linux, macOS, Windows) - via direct Rust compilation
- **Future**: Mobile (iOS/Android), other language bindings

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Game State Management** | Track inning progression, base runners, scoring, and substitutions |
| **Statistics Calculation** | Calculate batting average, ERA, OPS, and other statistics |
| **Roster Management** | Track player status, bench players, and substitution history |
| **Multi-Game Archiving** | Store and retrieve multiple games in Baselom JSON format |

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

### 1. Standard Library Conditional Usage

The core logic is designed to be `#![no_std]` compatible with the `alloc` crate for heap allocation. However, some features require the standard library and are gated behind feature flags.

```rust
// Core types and logic - no_std compatible
#[cfg(not(feature = "std"))]
extern crate alloc;

#[cfg(not(feature = "std"))]
use alloc::{string::String, vec::Vec};

// JSON serialization requires std feature
#[cfg(feature = "std")]
use serde_json;
```

**Important Note on `no_std` and JSON Serialization**:

`serde_json` requires the standard library (`std`) because it:
- Uses `std::io::Write` for serialization
- Depends on `std::error::Error` for error handling
- Uses `std::collections::HashMap` for JSON objects

**Serialization Strategy by Environment**:

| Environment | Serialization Format | Feature Flags | Notes |
|-------------|---------------------|---------------|-------|
| **Native (Python/CLI)** | JSON (`serde_json`) | `--features std` | Human-readable, interoperable |
| **WASM (Browser)** | JSON (`serde_json`) | `--features std` | Standard library available in WASM |
| **Embedded / no_std** | Binary (`postcard`) | `--no-default-features --features alloc` | Compact, no_std compatible |
| **Cross-platform Archive** | JSON | `--features std` | For data exchange between platforms |

**Cross-Platform Serialization Compatibility**:

The requirement "Rust and Python produce identical serialized output" applies ONLY to JSON serialization with `std` feature enabled. For `no_std` environments:

1. **Use binary formats** (`postcard`, `bincode`) for internal storage
2. **Convert to JSON** at boundary when interoperating with Python/external systems
3. **Maintain separate serialization paths**:
   - Internal: Binary format (no_std safe)
   - External: JSON format (requires std feature)

**Example: no_std WASM Build with External JSON Support**

```rust
// Internal state serialization (no_std)
#[cfg(not(feature = "std"))]
fn serialize_state_internal(state: &GameState) -> Result<Vec<u8>, Error> {
    postcard::to_allocvec(state).map_err(|e| Error::Serialization(e))
}

// External JSON serialization (std required)
#[cfg(feature = "std")]
fn serialize_state_json(state: &GameState) -> Result<String, Error> {
    serde_json::to_string(state).map_err(|e| Error::Serialization(e))
}

// WASM binding (can use either depending on build features)
#[wasm_bindgen]
pub fn export_state_json(state: &GameState) -> Result<String, JsValue> {
    #[cfg(feature = "std")]
    {
        serialize_state_json(state).map_err(|e| JsValue::from_str(&e.to_string()))
    }
    
    #[cfg(not(feature = "std"))]
    {
        // For no_std WASM, must convert via binary format
        let binary = serialize_state_internal(state)?;
        // Convert to hex string or base64 for transmission
        Ok(hex::encode(binary))
    }
}
```

**Recommended Build Configurations**:

```toml
# Cargo.toml
[features]
default = ["std"]
std = ["serde_json"]           # Enable JSON + std library
alloc = []                     # Enable heap allocation only
python = ["pyo3", "std"]       # Python bindings (requires std)
wasm = ["wasm-bindgen"]        # WASM bindings (can work with or without std)

[dependencies]
serde = { version = "1.0", default-features = false, features = ["derive", "alloc"] }
serde_json = { version = "1.0", optional = true }  # Only with std feature
postcard = { version = "1.0", default-features = false, features = ["alloc"] }
```

```bash
# Build examples

# Python bindings (requires std for JSON)
maturin build --release --features python,std

# WASM with std (recommended for browser use)
wasm-pack build --target web --features wasm,std

# WASM without std (embedded/minimal)
cargo build --target wasm32-unknown-unknown --no-default-features --features wasm,alloc

# Native CLI with JSON
cargo build --release --features std
```

**Testing Cross-Platform Serialization**:

```rust
#[cfg(all(test, feature = "std"))]
mod tests {
    use super::*;
    
    #[test]
    fn test_rust_python_json_compatibility() {
        let state = create_test_state();
        
        // Serialize in Rust
        let rust_json = serde_json::to_string(&state).unwrap();
        
        // Parse back
        let parsed: GameState = serde_json::from_str(&rust_json).unwrap();
        
        // Verify canonical form matches
        let canonical1 = canonical_json_bytes(&state);
        let canonical2 = canonical_json_bytes(&parsed);
        assert_eq!(canonical1, canonical2);
    }
}
```

See [Serialization](./serialization.md#cross-platform-serialization) for complete details on JSON canonicalization and cross-platform compatibility.

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

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
│    (Baseball Simulators, Real Game Scorekeeping, Analytics Systems)          │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python API Layer                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ models.py   │  │ engine.py    │  │ validators.py  │  │ serializer.py │  │
│  │ (Type Hints)│  │ (Wrappers)   │  │ (Validation)   │  │ (JSON I/O)    │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │exceptions.py│  │statistics.py │  │  roster.py     │  │  archive.py   │  │
│  │ (Errors)    │  │ (Stats Calc) │  │ (Player Mgmt)  │  │ (Multi-Game)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ PyO3 FFI Bindings
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Rust Core Engine                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ models.rs   │  │ engine.rs    │  │ validators.rs  │  │ statistics.rs │  │
│  │ (Data Types)│  │ (FSM Logic)  │  │ (State Check)  │  │ (Stats Calc)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ errors.rs   │  │ lib.rs       │  │  roster.rs     │  │  archive.rs   │  │
│  │ (Error Types)│ │ (Entry Point)│  │ (Player Mgmt)  │  │ (Multi-Game)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Single Responsibility

Baselom Core is **only** responsible for:

- Rule compliance checking
- State transitions
- Event generation
- **Statistics calculation** (batting average, ERA, etc.)
- **Roster management** (player status, substitution tracking)
- **Multi-game archiving** (storing and retrieving game data)

It does **not** handle:

- Player abilities or skill simulation
- Randomness or probability
- Game strategy or AI
- User interface
- Network communication
- External data persistence (uses JSON for data exchange)

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

Every state change produces an event with **envelope/payload structure**:

```json
{
  "envelope": {
    "event_id": "a1b2c3d4...",
    "event_type": "hit.v1",
    "schema_version": "1",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "payload": {
    "game_id": "game-001",
    "inning": 3,
    "top": true,
    "batter_id": "player_123",
    "pitcher_id": "player_456",
    "hit_type": "single",
    "runner_advances": [
      {"runner_id": "player_789", "from_base": 1, "to_base": 3}
    ]
  }
}
```

**Key Design Decisions:**
- `event_id` is **content-based** (SHA-256 of payload), not a UUID
- Timestamps are in envelope, NOT in the ID calculation
- Payload contains only **essential facts**, not derived values (no `rbi`)
- Same logical event always produces same `event_id`

Events enable:
- Full game replay
- Semantic equality detection (same play = same ID)
- Deduplication in storage
- Analytics and statistics
- External system integration

### 5. Content-Addressed Storage

Events and snapshots use **content-addressed identification**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event Storage Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────────────────┐   │
│  │  Events Index   │         │      Payload Store          │   │
│  │ (sequence_num,  │────────▶│  (event_id → payload_bytes) │   │
│  │  event_id)      │         │  Content-addressed          │   │
│  └─────────────────┘         └─────────────────────────────┘   │
│           │                                                      │
│           │ Periodic                                            │
│           ▼                                                      │
│  ┌─────────────────────────────┐                                │
│  │     Snapshot Store          │                                │
│  │  (snapshot_id → state)      │                                │
│  │  For fast replay            │                                │
│  └─────────────────────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Benefits:
- **Deduplication**: Identical payloads share storage
- **Immutability**: Append-only, no overwrites
- **Integrity**: Hash-based IDs enable verification
- **Fast Replay**: Snapshots skip replaying old events

See [Serialization - Event History Storage Architecture](./serialization.md#event-history-storage-architecture) for details.

## Component Details

### Rust Core (`src/`)

| File | Responsibility |
|------|----------------|
| `lib.rs` | PyO3 module entry point, exports |
| `models.rs` | Core data structures |
| `engine.rs` | FSM transition logic |
| `validators.rs` | State validation rules |
| `errors.rs` | Error type definitions |
| `statistics.rs` | Statistics calculation logic |
| `roster.rs` | Roster and player management |
| `archive.rs` | Multi-game archive handling |
| `serializer.rs` | Canonical JSON and hashing |

### Python Layer (`baselom_core/`)

| File | Responsibility |
|------|----------------|
| `__init__.py` | Package exports |
| `models.py` | Python dataclass definitions, type hints |
| `engine.py` | Wrapper functions around Rust core |
| `validators.py` | Additional Python-side validation |
| `serializer.py` | JSON serialization/deserialization, canonical JSON |
| `exceptions.py` | Python exception hierarchy |
| `statistics.py` | Statistics functions and aggregation |
| `roster.py` | Roster management functions |
| `archive.py` | Multi-game archive import/export |

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

### Performance Targets and Benchmarking

**Important**: Performance targets are **environment-specific** and depend on:
- CPU architecture and clock speed
- Build configuration (Release vs Debug)
- Execution context (pure Rust vs PyO3 bindings)
- System load and resource availability

#### Target Performance Goals (Reference Environment)

**Reference Environment Specification:**
- CPU: Intel Xeon (GitHub Actions standard runner) or equivalent 2-4 core CPU @ 2.0+ GHz
- Build: `--release` (optimizations enabled)
- Context: Direct Rust calls (not Python bindings)
- Conditions: Single-threaded, isolated execution

Note: GitHub Actions runners use varying Intel/AMD CPUs. Benchmarks should specify actual CPU model used.

| Operation | Target (Rust Core) | Target (Python via PyO3) | Notes |
|-----------|-------------------|-------------------------|-------|
| `apply_pitch()` | < 100μs | < 300μs | PyO3 overhead adds ~2-3x latency |
| `validate_state()` | < 50μs | < 150μs | Includes full invariant checking |
| State serialization (JSON) | < 100μs | < 200μs | Canonical JSON generation |
| Full game simulation (9 innings, ~300 pitches) | < 50ms | < 200ms | End-to-end including state transitions |

**Debug Build Performance**: Expect 5-10x slower performance in Debug builds. Always use `--release` for benchmarking.

**WASM Performance** (Future, v0.2.0+): WASM builds may be 2-3x slower than native due to:
- Limited CPU instruction set
- Memory access patterns
- Browser JavaScript interop overhead

#### Benchmark Execution

Benchmarks MUST document their execution environment:

```bash
# Rust benchmarks
cargo bench --features bench -- --save-baseline reference

# Python benchmarks
pytest tests/test_performance.py --benchmark-only --benchmark-json=benchmark.json

# Record environment
echo "CPU: $(lscpu | grep 'Model name')" >> benchmark_env.txt
echo "Rust: $(rustc --version)" >> benchmark_env.txt
echo "Build: release" >> benchmark_env.txt
```

#### CI Benchmark Configuration

GitHub Actions benchmark job specification:

```yaml
benchmark:
  runs-on: ubuntu-latest  # Standard runner (2-core CPU)
  steps:
    - name: Run benchmarks
      run: |
        cargo bench --release
        pytest --benchmark-only
    
    - name: Record environment
      run: |
        echo "Runner: ${{ runner.os }} - ${{ runner.arch }}"
        lscpu > ci_cpu_info.txt
        cat /proc/cpuinfo >> ci_cpu_info.txt
```

#### Performance Regression Detection

Benchmarks should be monitored for regressions:
- **Warning threshold**: 20% slower than baseline
- **Failure threshold**: 50% slower than baseline
- **Baseline update**: When intentional changes affect performance

#### Optimization Priority

Performance optimization should focus on:
1. **Hot path operations**: `apply_pitch()`, state transitions
2. **Serialization**: Canonical JSON generation (used frequently)
3. **Validation**: Only check invariants when necessary
4. **Memory allocation**: Minimize allocations in core engine

**Non-goals**: 
- Sub-microsecond latencies (not required for baseball simulation)
- Extreme optimization at cost of code clarity
- Platform-specific SIMD optimizations (maintain portability)

#### Performance Testing Documentation

All benchmark results SHOULD include:
- Hardware specification (CPU model, RAM, storage type)
- Software environment (OS, Rust version, Python version)
- Build configuration (release/debug, features enabled)
- Test conditions (single-threaded, system load)
- Statistical summary (mean, median, std dev, min, max)

Example benchmark report:

```
Environment:
  CPU: Intel Core i7-9750H @ 2.60GHz
  OS: Ubuntu 22.04
  Rust: 1.75.0
  Python: 3.11.5
  Build: --release

Results (mean of 1000 iterations):
  apply_pitch()     : 87μs  ± 12μs  [✓ within target]
  validate_state()  : 43μs  ± 8μs   [✓ within target]
  Full game (9 inn) : 45ms  ± 7ms   [✓ within target]
```

*Note: Targets are aspirational for optimized Release builds. Actual performance will be documented as benchmarks are implemented and measured across different environments.*

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

| Crate | Purpose | WASM Compatible | Notes |
|-------|---------|-----------------|-------|
| `serde` | Serialization | ✅ Yes | Core derive macros work in all environments |
| `serde_json` | JSON support | ⚠️ Requires `std` | Use `--features std` for JSON; for no_std WASM, use binary formats |
| `thiserror` | Error handling | ✅ Yes | |
| `postcard` | Binary serialization | ✅ Yes (no_std) | Alternative for no_std environments |

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
