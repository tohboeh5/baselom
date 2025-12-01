# Baselom Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)

**Lightweight, pure game-state engine for baseball.**

Baselom Core implements inning progression, base/runner state, scoring, and substitutions as an immutable, testable Finite State Machine (FSM). Like [Polars](https://github.com/pola-rs/polars), the core engine is written in Rust for maximum performance and exposed to Python via PyO3/maturin.

## 🎯 Use Cases

Baselom Core is designed for both **game simulations** and **real-world game management**:

| Use Case | Description |
|----------|-------------|
| **⚾ Real Game Score Management** | Track actual baseball games with official scoring, substitutions, and statistics |
| **🎮 Game Simulations** | Build baseball video games, fantasy baseball engines, or AI training environments |
| **📊 Statistics & Analytics** | Calculate batting averages, ERA, and other statistics across multiple games |
| **📝 Score Archiving** | Store and replay complete game data using Baselom's multi-game archive format |

## ✨ Key Features

- **🎯 Single Responsibility**: Only handles rule compliance and state transitions. No randomness, probabilities, player abilities, or tactics.
- **🔒 Immutable State**: `GameState` is immutable—state changes always return a new instance.
- **✅ Testable**: Fine-grained use cases can be covered by tests with >90% coverage target.
- **⚙️ Configurable Rules**: DH, extra innings, tiebreaker rules externalized via `GameRules`.
- **📝 Event-Oriented**: All plays output as `Event` objects, immediately serializable to JSON.
- **⚡ High Performance**: Rust core with Python bindings via PyO3/maturin.
- **📊 Statistics Engine**: Calculate batting averages, ERA, OPS, and other statistics across multiple games.
- **👥 Roster Management**: Track player states including bench, active roster, and substitution history.
- **📦 Multi-Game Archive**: Store and retrieve complete game data in Baselom's native JSON format.

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

# From source
git clone https://github.com/tohboeh5/baselom.git
cd baselom
pip install maturin
maturin develop
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

# Apply a pitch result (ball put in play resulting in a single)
state, event = apply_pitch(state, 'in_play', rules, batted_ball_result='single')
print(event)
# {'event_type': 'single', 'batter_id': 'a1', 'rbi': 0, ...}

# State is immutable - original unchanged
print(state.bases)  # ('a1', None, None)
```

## 📊 Core Data Models

### GameState

Immutable representation of the current game state:

```python
from typing import Literal, Tuple, Dict, Optional, Any

@dataclass(frozen=True)
class GameState:
    inning: int                     # 1-based inning number
    top: bool                       # True = top of inning
    outs: int                       # 0..2
    balls: int                      # 0..3
    strikes: int                    # 0..2
    bases: Tuple[Optional[str], Optional[str], Optional[str]]
    score: Dict[str, int]           # {'home': int, 'away': int}
    batting_team: Literal['home', 'away']
    fielding_team: Literal['home', 'away']
    current_pitcher_id: Optional[str]
    current_batter_id: Optional[str]
    lineup_index: Dict[str, int]    # {'home': 0-8, 'away': 0-8}
    lineups: Dict[str, Tuple[str, ...]]
    pitchers: Dict[str, str]        # {'home': pitcher_id, 'away': pitcher_id}
    inning_runs: Dict[str, int]
    game_status: Literal['in_progress', 'final', 'suspended']
    event_history: Tuple[Dict[str, Any], ...]
    rules_version: str
    created_at: str                 # ISO 8601 timestamp
```

For complete field specifications, see [Data Models](./docs/data-models.md).

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

### Statistics Functions

| Function | Description |
|----------|-------------|
| `calculate_batting_average()` | Calculate batting average from player stats |
| `calculate_era()` | Calculate earned run average for pitcher |
| `calculate_player_stats()` | Generate comprehensive stats for a player |
| `aggregate_stats()` | Aggregate stats across multiple games |

### Multi-Game Archive Functions

| Function | Description |
|----------|-------------|
| `create_game_archive()` | Create a new multi-game archive |
| `add_game_to_archive()` | Add a completed game to archive |
| `export_archive()` | Export archive to Baselom JSON format |
| `import_archive()` | Import archive from Baselom JSON format |

### Roster Management Functions

| Function | Description |
|----------|-------------|
| `create_roster()` | Create a team roster |
| `update_player_status()` | Update player status (active/bench/injured) |
| `get_player_game_stats()` | Get per-game statistics for a player |

## 📁 Project Structure

```
baselom/
├─ src/                    # Rust source
│  ├─ lib.rs
│  ├─ models.rs
│  ├─ engine.rs
│  ├─ statistics.rs
│  ├─ roster.rs
│  └─ archive.rs
├─ baselom_core/           # Python package
│  ├─ __init__.py
│  ├─ models.py
│  ├─ engine.py
│  ├─ serializer.py
│  ├─ exceptions.py
│  ├─ validators.py
│  ├─ statistics.py
│  ├─ roster.py
│  └─ archive.py
├─ tests/
├─ docs/                   # Specifications
├─ Cargo.toml
├─ pyproject.toml
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

Contributions are welcome! Please read the development guide in `docs/development.md` before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `pytest` and `cargo test`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

*Baselom Core is designed to be the foundation for baseball simulation systems and real-world game management, providing a reliable, tested, and high-performance rules engine*.
