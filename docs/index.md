# Baselom Core Documentation

Welcome to the Baselom Core specification documentation.

## Overview

Baselom Core is a lightweight, pure game-state engine for baseball that implements:

- Inning progression
- Base/runner state management
- Scoring
- Substitutions

All implemented as an **immutable, testable Finite State Machine (FSM)**.

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Single Responsibility** | Only handles rule compliance and state transitions |
| **Purity** | `GameState` is immutable; changes return new instances |
| **Testability** | Fine-grained test coverage (>90% target) |
| **Configurability** | Rules externalized via `GameRules` |
| **Event-Oriented** | All plays output as JSON-serializable `Event` objects |
| **High Performance** | Rust core with Python bindings (PyO3/maturin) |

## Documentation Index

### Core Specifications

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | System architecture, component design, Rust/Python hybrid structure, data flow diagrams |
| [Data Models](./data-models.md) | Complete specifications for `GameState`, `GameRules`, `Event`, and all enumerations |
| [API Reference](./api-reference.md) | Public function signatures, parameters, return types, and usage examples |

### Rules & Logic

| Document | Description |
|----------|-------------|
| [Rules Logic](./rules-logic.md) | Baseball rule processing specifications, state transitions, scoring rules, base running |

### Technical

| Document | Description |
|----------|-------------|
| [Serialization](./serialization.md) | JSON schemas, serialization/deserialization functions, versioning, migration |
| [Error Handling](./error-handling.md) | Exception hierarchy, error codes, handling patterns, Rust-Python error propagation |

### Development

| Document | Description |
|----------|-------------|
| [Testing](./testing.md) | Test strategy, test categories, fixtures, coverage targets, CI testing |
| [Development Guide](./development.md) | Environment setup, build commands, debugging, CI/CD pipeline, contribution guidelines |
| [Versioning](./versioning.md) | Semantic versioning policy, compatibility guarantees, deprecation process, migration |

## Quick Start

### Installation

```bash
# From PyPI (when published)
pip install baselom-core

# From source
git clone https://github.com/tohboeh5/baselom.git
cd baselom
pip install maturin
maturin develop
```

### Basic Usage

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

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Python API Layer                          │
│  (baselom_core package - type hints, convenience APIs)       │
└─────────────────────┬───────────────────────────────────────┘
                      │ PyO3 Bindings
┌─────────────────────▼───────────────────────────────────────┐
│                    Rust Core Engine                          │
│  (models, engine, validators - high-performance FSM)         │
└─────────────────────────────────────────────────────────────┘
```

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
