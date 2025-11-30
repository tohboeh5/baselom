# Baselom Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-1.83+-orange.svg)](https://www.rust-lang.org/)

**Lightweight, pure game-state engine for baseball.**

Baselom Core implements inning progression, base/runner state, scoring, and substitutions as an immutable, testable Finite State Machine (FSM). Like [Polars](https://github.com/pola-rs/polars), the core engine is written in Rust for maximum performance and exposed to Python via PyO3/maturin.

## ✨ Key Features

- **🎯 Single Responsibility**: Only handles rule compliance and state transitions. No randomness, probabilities, player abilities, or tactics.
- **🔒 Immutable State**: `GameState` is immutable—state changes always return a new instance.
- **✅ Testable**: Fine-grained use cases can be covered by tests with >90% coverage target.
- **⚙️ Configurable Rules**: DH, extra innings, tiebreaker rules externalized via `GameRules`.
- **📝 Event-Oriented**: All plays output as `Event` objects, immediately serializable to JSON.
- **⚡ High Performance**: Rust core with Python bindings via PyO3/maturin.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Python API Layer                      │
│  (baselom_core package - type hints, convenience APIs)   │
└─────────────────────┬───────────────────────────────────┘
                      │ PyO3 Bindings
┌─────────────────────▼───────────────────────────────────┐
│                    Rust Core Engine                      │
│  (models, engine, validators - high-performance FSM)     │
└─────────────────────────────────────────────────────────┘
```

## 📦 Installation

```bash
# From PyPI (when published)
pip install baselom-core

# From source (recommended: use mise)
git clone https://github.com/tohboeh5/baselom.git
cd baselom
mise install && mise run install
mise run build
```

## 🚀 Quick Start

```python
from baselom_core import initial_game_state, apply_pitch, GameRules

# Initialize game with default rules
rules = GameRules(designated_hitter=False)
state = initial_game_state(
    home_lineup=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'],
    away_lineup=['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
    rules=rules
)

# Apply a pitch result
state, event = apply_pitch(state, 'hit_single', rules)
print(event)
# {'type': 'single', 'batter': 'a1', 'rbi': 0, ...}

# State is immutable - original unchanged
print(state.bases)  # ('a1', None, None)
```

## 📊 Core Data Models

### GameState

Immutable representation of the current game state:

```python
@dataclass(frozen=True)
class GameState:
    inning: int                     # 1-based inning number
    top: bool                       # True = top of inning
    outs: int                       # 0..2
    bases: Tuple[Optional[str], Optional[str], Optional[str]]
    score: Dict[str, int]           # {'home': int, 'away': int}
    batting_team: str               # 'home' or 'away'
    fielding_team: str
    current_pitcher_id: Optional[str]
    current_batter_id: Optional[str]
    lineup_index: Dict[str, int]
    inning_runs: Dict[str, int]
    event_history: Tuple[dict, ...]
    rules_version: str
```

### GameRules

Configurable rule set:

```python
@dataclass(frozen=True)
class GameRules:
    designated_hitter: bool = False
    max_innings: Optional[int] = 9
    extra_innings_tiebreaker: Optional[str] = None
    allow_balks: bool = True
    allow_wild_pitch: bool = True
    runner_advances_on_error: bool = True
    # ... more options
```

## 🔧 Public API

| Function | Description |
|----------|-------------|
| `initial_game_state()` | Create initial game state |
| `validate_state()` | Validate state consistency |
| `apply_pitch()` | Process pitch result → new state + event |
| `apply_batter_action()` | Process batter/runner action |
| `force_substitution()` | Handle player substitutions |
| `end_half_inning()` | Transition to next half-inning |

## 📁 Project Structure

```
baselom/
├─ src/                    # Rust source
│  ├─ lib.rs
│  ├─ models.rs
│  ├─ engine.rs
│  ├─ validators.rs
│  └─ errors.rs
├─ baselom_core/           # Python package
│  ├─ __init__.py
│  ├─ models.py
│  ├─ engine.py
│  ├─ serializer.py
│  ├─ exceptions.py
│  └─ validators.py
├─ tests/
├─ docs/                   # Specifications
├─ Cargo.toml
├─ pyproject.toml
├─ mise.toml               # Development tasks
└─ README.md
```

## 📖 Documentation

Full specifications available in [`docs/`](./docs/):

- [Architecture](./docs/architecture.md)
- [Data Models](./docs/data-models.md)
- [API Reference](./docs/api-reference.md)
- [Rules Logic](./docs/rules-logic.md)
- [Serialization](./docs/serialization.md)
- [Error Handling](./docs/error-handling.md)
- [Testing](./docs/testing.md)
- [Development](./docs/development.md)
- [Versioning](./docs/versioning.md)

## 🤝 Contributing

Contributions are welcome! See the [Development Guide](./docs/development.md) for:
- Quick setup with mise
- WASM-compatible development rules
- Available commands (`mise run format`, `lint`, `test`)

```bash
# Quick start
git clone https://github.com/tohboeh5/baselom.git
cd baselom
mise install && mise run install
mise run test  # Run all tests
```

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

*Baselom Core is designed to be the foundation for baseball simulation systems, providing a reliable, tested, and high-performance rules engine*.
