# Baselom Core Documentation

Welcome to the Baselom Core specification documentation.

## Overview

Baselom Core is a lightweight, pure game-state engine for baseball that implements:

- Inning progression
- Base/runner state management
- Scoring
- Substitutions
- **Statistics calculation** (batting average, ERA, etc.)
- **Multi-game data archiving**
- **Roster and player state management**

All implemented as an **immutable, testable Finite State Machine (FSM)**.

## Use Cases

Baselom Core is designed for both **game simulations** and **real-world game management**:

| Use Case | Description |
|----------|-------------|
| **⚾ Real Game Score Management** | Track actual baseball games with official scoring, substitutions, and statistics |
| **🎮 Game Simulations** | Build baseball video games, fantasy baseball engines, or AI training environments |
| **📊 Statistics & Analytics** | Calculate batting averages, ERA, and other statistics across multiple games |
| **📝 Score Archiving** | Store and replay complete game data using Baselom's multi-game archive format |

## Release Roadmap

| Phase | Platform | Status | Description |
|-------|----------|--------|-------------|
| **v0.1.0** | **Python** | 🚧 In Development | Initial release as Python library via PyO3/maturin |
| v0.2.0 | WASM | Planned | WebAssembly build for browser and Node.js |
| v0.3.0+ | Others | Future | Additional language bindings as needed |

> **Note**: The initial release focuses on Python. The architecture is WASM-compatible from the start to enable future multi-platform support.

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Single Responsibility** | Only handles rule compliance and state transitions |
| **Deep Immutability** | `GameState` and all nested objects are immutable; uses `Tuple`, `Mapping` instead of `List`, `Dict` |
| **Testability** | Fine-grained test coverage (>90% target) |
| **Configurability** | Rules externalized via `GameRules` |
| **Event-Oriented** | All plays output as envelope/payload `Event` objects with content-based IDs |
| **Deterministic Serialization** | Canonical JSON (RFC 8785) enables content-addressed storage and semantic comparison |
| **High Performance** | Rust core with multiple platform bindings |
| **Multi-Platform** | WASM-first design enabling browser, Node.js, Python, and native execution |
| **Versatility** | Suitable for both game simulations and real-world score management |

## Documentation Index

### Core Specifications

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | System architecture, component design, Rust/Python hybrid structure, data flow diagrams |
| [Data Models](./data-models.md) | Complete specifications for `GameState`, `GameRules`, `Event`, roster, and statistics models |
| [API Reference](./api-reference.md) | Public function signatures, parameters, return types, and usage examples |

### Statistics & Multi-Game

| Document | Description |
|----------|-------------|
| [Statistics](./data-models.md#statistics-models) | Player statistics models, calculation methods, aggregation across games |
| [Multi-Game Archive](./serialization.md#multi-game-archive-format) | JSON format for storing multiple games with metadata |

### Rules & Logic

| Document | Description |
|----------|-------------|
| [Rules Logic](./rules-logic.md) | Baseball rule processing specifications, state transitions, scoring rules, base running |

### Technical

| Document | Description |
|----------|-------------|
| [Serialization](./serialization.md) | Canonical JSON, content-based IDs, event envelope/payload structure, versioning, migration, event history storage |
| [Error Handling](./error-handling.md) | Exception hierarchy, error codes, handling patterns, Rust-Python error propagation |

### Development

| Document | Description |
|----------|-------------|
| [Testing](./testing.md) | Test strategy, test categories, fixtures, coverage targets, CI testing, cross-platform interoperability tests |
| [Development Guide](./development.md) | Environment setup, build commands, debugging, CI/CD pipeline, contribution guidelines |
| [Versioning](./versioning.md) | Semantic versioning policy, compatibility guarantees, deprecation process, migration |

## Quick Start

### Installation

```bash
# Python (from PyPI when published)
pip install baselom-core

# Python (from source with uv - recommended)
git clone https://github.com/tohboeh5/baselom.git
cd baselom
uv sync
uv run maturin develop

# Python (from source with pip)
git clone https://github.com/tohboeh5/baselom.git
cd baselom
pip install maturin
maturin develop

# JavaScript/TypeScript (future - from npm when published)
npm install baselom-core
```

### Basic Usage

#### Python

```python
from baselom_core import initial_game_state, apply_pitch, GameRules

# Initialize game
rules = GameRules(designated_hitter=False)
state = initial_game_state(
    home_lineup=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'],
    away_lineup=['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
    rules=rules
)

# Process pitches
state, event = apply_pitch(state, 'ball', rules)
state, event = apply_pitch(state, 'strike_called', rules)
state, event = apply_pitch(state, 'in_play', rules, batted_ball_result='single')
```

#### JavaScript/TypeScript (WASM - Future)

> **Note**: WASM support is planned for v0.2.0. The API will mirror Python for consistency.

```typescript
import init, { initialGameState, applyPitch, GameRules } from 'baselom-core';

// Initialize WASM module
await init();

// Initialize game (API mirrors Python for consistency)
const rules = new GameRules({ designatedHitter: false });
const state = initialGameState(
  ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'],
  ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
  rules
);

// Process pitches
const [newState, event] = applyPitch(state, 'ball', rules);
console.log(JSON.stringify(event));
```

## Architecture Overview

Baselom Core is designed as a **multi-platform library** with WASM support as a primary target:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Python    │  │  Browser /  │  │    Node.js /        │  │
│  │   (PyO3)    │  │  Web App    │  │    Native           │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼───────────────────┼──────────────┘
          │                │                   │
          ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Rust Core Engine (WASM-Compatible)              │
│         (models, engine, validators - pure FSM)              │
└─────────────────────────────────────────────────────────────┘
```

The core is intentionally designed without I/O or system dependencies, enabling seamless compilation to WebAssembly for browser and edge environments.

For detailed architecture information, see [Architecture](./architecture.md).

## Key Concepts

### Immutable State

All state objects are immutable. State changes always return new instances:

```python
new_state, event = apply_pitch(old_state, pitch_result, rules)
# old_state remains unchanged
```

### Event Sourcing

Every state transition produces an event that can be:
- Serialized to JSON
- Used for replay
- Sent to external systems
- Stored for analytics

### Configurable Rules

Rules can be customized for different baseball variants:

```python
# MLB Rules (2024)
rules = GameRules(
    designated_hitter=True,
    extra_innings_tiebreaker='runner_on_second'
)

# Little League Rules
rules = GameRules(
    max_innings=6,
    mercy_rule_enabled=True,
    mercy_rule_threshold=10
)
```

## Quick Links

- [GitHub Repository](https://github.com/tohboeh5/baselom)
- [README](../README.md)
- [Changelog](../CHANGELOG.md)

## Contributing

Contributions are welcome! Please read the [Development Guide](./development.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `pytest` and `cargo test`
5. Submit a pull request

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

*Version: v0.1.0 (Draft)*
