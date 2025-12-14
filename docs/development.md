# Development Guide

> **Note**: This guide focuses on the **mise-based development workflow** introduced in v0.1.0+. For detailed manual setup instructions, see the sections below or the original documentation.

## Quick Start with mise

**Recommended**: Use [mise](https://mise.jdx.dev/) for consistent development environment across all platforms.

```bash
# Clone and setup
git clone https://github.com/tohboeh5/baselom.git
cd baselom
mise install       # Install Python, Rust, uv
mise run install   # Install dependencies + WASM target
```

### Daily Development Commands

```bash
mise run format    # Format all code (Rust + Python)
mise run lint      # Lint all code (format check + clippy + ruff)
mise run test      # Run all tests (Rust + Python + WASM check)
mise run build     # Build Python bindings for development
```

### Pre-commit Hooks

Pre-commit hooks automatically run `format` and `lint` on every commit:

```bash
pre-commit install  # Already done in devcontainer
# Install wasm-pack
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# Or via cargo
cargo install wasm-pack

# Add WASM target
rustup target add wasm32-unknown-unknown

# Verify installation
wasm-pack --version
```

## Project Structure

```
baselom/
├── src/                      # Rust source code
│   ├── lib.rs               # Module entry point, PyO3 exports
│   ├── models.rs            # Data structures
│   ├── engine.rs            # FSM logic
│   ├── validators.rs        # State validation
│   ├── errors.rs            # Error types
│   ├── statistics.rs        # Statistics calculation
│   ├── roster.rs            # Roster management
│   └── archive.rs           # Multi-game archive
├── baselom_core/            # Python package
│   ├── __init__.py          # Package exports
│   ├── models.py            # Python type hints
│   ├── engine.py            # Python wrappers
│   ├── validators.py        # Python validation
│   ├── serializer.py        # JSON handling
│   ├── exceptions.py        # Exception classes
│   ├── statistics.py        # Statistics functions
│   ├── roster.py            # Roster management
│   └── archive.py           # Multi-game archive I/O
├── tests/                   # Test files
│   ├── conftest.py          # Pytest fixtures
│   ├── test_models.py       # Model tests
│   ├── test_engine.py       # Engine tests
│   ├── test_serialization.py
│   ├── test_statistics.py   # Statistics tests
│   ├── test_roster.py       # Roster tests
│   ├── test_archive.py      # Archive tests
│   └── fixtures/            # Test data
├── docs/                    # Documentation
├── Cargo.toml               # Rust dependencies
├── pyproject.toml           # Python project config
└── README.md
```

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** to Rust and/or Python code

3. **Rebuild**
   ```bash
   uv run maturin develop  # With uv
   # or: maturin develop   # With pip
   ```

4. **Run tests**
   ```bash
   cargo test                 # Rust tests
   uv run pytest              # Python tests (with uv)
   # or: pytest               # Python tests (with pip)
   ```

5. **Lint and format**
   ```bash
   cargo fmt          # Format Rust
   cargo clippy       # Lint Rust
   uv run ruff check .       # Lint Python (with uv)
   uv run ruff format .      # Format Python (with uv)
   uv run mypy baselom_core  # Type check Python (with uv)
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```

## WASM-Compatible Development Rules

**Important**: Follow these rules to ensure Rust code works seamlessly across Python, WASM, and native targets without refactoring.

### Core Principles

1. **Keep core logic platform-agnostic**: All game state logic lives in the core Rust modules (`models.rs`, `engine.rs`, `validators.rs`, `errors.rs`) without any platform-specific dependencies.

2. **Use feature flags for bindings only**: Platform-specific code (PyO3, wasm-bindgen) is conditionally compiled via feature flags. Core logic should never depend on these features.

3. **No I/O in core**: The core engine performs no I/O operations (file system, network, system time). All external data must be passed in as function arguments.

4. **Pure functions**: All state transitions are pure functions: `(State, Input) → (NewState, Event)`. No side effects.

5. **Serialization-friendly types**: Use types that serialize cleanly to JSON (the common interchange format for all platforms).

### Checklist Before Adding New Code

Before implementing any new feature, verify:

- [ ] Does the code use only `serde`, `serde_json`, and `thiserror` dependencies? (These are WASM-compatible)
- [ ] Is the code free of `std::fs`, `std::net`, `std::time::SystemTime`?
- [ ] Are all public types `Serialize + Deserialize`?
- [ ] Does the function have no side effects (pure function)?
- [ ] Can the types be represented in both Python (via PyO3) and JavaScript (via wasm-bindgen)?

### Code Organization

```
src/
├── lib.rs           # Entry point with conditional platform bindings
├── models.rs        # Core data types (platform-agnostic)
├── engine.rs        # FSM logic (platform-agnostic)
├── validators.rs    # State validation (platform-agnostic)
└── errors.rs        # Error types (platform-agnostic)
```

- **Core modules** (`models.rs`, `engine.rs`, etc.): No `#[cfg]` attributes, no platform imports
- **lib.rs**: Contains `#[cfg(feature = "python")]` and `#[cfg(feature = "wasm")]` sections for bindings

### Example: Adding a New Function

```rust
// ✅ Good: Platform-agnostic core function
pub fn calculate_score(state: &GameState) -> Score {
    // Pure logic, no I/O, no platform dependencies
    Score { home: state.runs_home, away: state.runs_away }
}

// ❌ Bad: Platform-specific in core
pub fn calculate_score(state: &GameState) -> Score {
    println!("Calculating..."); // I/O side effect
    let now = std::time::SystemTime::now(); // System call
    // ...
}
```

## CI/CD

Every push and PR automatically runs:
1. **Lint job**: `mise run lint` - Format check + clippy + ruff
2. **Test job**: `mise run test` - Rust tests + Python tests + WASM compilation check

This ensures platform compatibility is verified on every commit.

## Available mise Tasks

| Task | Description |
|------|-------------|
| `mise run install` | Install all dependencies |
| `mise run format` | Format Rust + Python code |
| `mise run lint` | Lint all code (includes format check) |
| `mise run test` | Run all tests (Rust + Python + WASM check) |
| `mise run build` | Build Python bindings (development) |
| `mise run build-release` | Build Python bindings (release) |
| `mise run build-wasm` | Build WASM target |
| `mise run check-all` | Verify all targets compile |

### Individual Tasks

```bash
mise run format-rust     # Format Rust only
mise run format-python   # Format Python only
mise run lint-rust       # Lint Rust only
mise run lint-python     # Lint Python only
mise run test-rust       # Test Rust only
mise run test-python     # Test Python only
mise run test-wasm       # WASM compilation check
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

Example: `feat(engine): add support for extra innings tiebreaker`

## See Also

- [Architecture](./architecture.md) - System design and multi-platform strategy
- [Data Models](./data-models.md) - Core data structures
- [API Reference](./api-reference.md) - Public API documentation
- [Testing](./testing.md) - Test strategy and coverage
- [Versioning](./versioning.md) - Version policy
