# Development Guide

## Overview

This guide covers setting up a development environment, building the project, and contributing to Baselom Core.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.9+ | Python runtime and tests |
| Rust | 1.70+ | Core engine development |
| Git | 2.0+ | Version control |

### Recommended Tools

| Tool | Purpose |
|------|---------|
| VS Code | IDE with Rust and Python support |
| rust-analyzer | Rust language server |
| Pylance | Python language server |
| ruff | Python linting |

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/tohboeh5/baselom.git
cd baselom
```

### 2. Setup Rust

```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version

# Install additional components
rustup component add clippy rustfmt
```

### 3. Setup Python

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Or install manually
pip install maturin pytest pytest-cov mypy ruff
```

### 4. Build the Project

```bash
# Development build (Python bindings)
maturin develop

# Release build
maturin build --release

# Rust only
cargo build
cargo build --release
```

## Project Structure

```
baselom/
├── src/                      # Rust source code
│   ├── lib.rs               # Module entry point, PyO3 exports
│   ├── models.rs            # Data structures
│   ├── engine.rs            # FSM logic
│   ├── validators.rs        # State validation
│   └── errors.rs            # Error types
├── baselom_core/            # Python package
│   ├── __init__.py          # Package exports
│   ├── models.py            # Python type hints
│   ├── engine.py            # Python wrappers
│   ├── validators.py        # Python validation
│   ├── serializer.py        # JSON handling
│   └── exceptions.py        # Exception classes
├── tests/                   # Test files
│   ├── conftest.py          # Pytest fixtures
│   ├── test_models.py       # Model tests
│   ├── test_engine.py       # Engine tests
│   ├── test_serialization.py
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
   maturin develop  # Rebuilds Python bindings
   ```

4. **Run tests**
   ```bash
   cargo test         # Rust tests
   pytest             # Python tests
   ```

5. **Lint and format**
   ```bash
   cargo fmt          # Format Rust
   cargo clippy       # Lint Rust
   ruff check .       # Lint Python
   ruff format .      # Format Python
   mypy baselom_core  # Type check Python
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(engine): add support for extra innings tiebreaker
fix(validation): handle edge case with empty lineup
docs(api): update apply_pitch documentation
test(scenarios): add walkoff home run test
```

## Building and Testing

### Rust Build Commands

```bash
# Debug build
cargo build

# Release build
cargo build --release

# Check without building
cargo check

# Run tests
cargo test

# Run specific test
cargo test test_name

# Run tests with output
cargo test -- --nocapture

# Run benchmarks
cargo bench

# Generate docs
cargo doc --open
```

### Python Build Commands

```bash
# Development build (links to Rust library)
maturin develop

# Development build with release optimization
maturin develop --release

# Build wheel
maturin build

# Build release wheel
maturin build --release

# Run tests
pytest

# Run with coverage
pytest --cov=baselom_core --cov-report=html

# Run specific test
pytest tests/test_engine.py::TestCountProcessing

# Type check
mypy baselom_core

# Lint
ruff check .
ruff check . --fix  # Auto-fix

# Format
ruff format .
```

## Debugging

### Rust Debugging

#### Using println!

```rust
fn apply_pitch_impl(state: &GameState, pitch: PitchResult) -> Result<...> {
    println!("Current state: {:?}", state);
    println!("Pitch result: {:?}", pitch);
    // ...
}
```

#### Using VS Code

1. Install "CodeLLDB" extension
2. Add launch configuration:
   ```json
   {
     "type": "lldb",
     "request": "launch",
     "name": "Debug Rust Tests",
     "cargo": {
       "args": ["test", "--no-run"]
     },
     "program": "${workspaceFolder}/target/debug/deps/baselom_core-xxxxx"
   }
   ```

### Python Debugging

#### Using pdb

```python
import pdb

def test_something():
    state = initial_game_state(...)
    pdb.set_trace()  # Breakpoint
    result = apply_pitch(state, 'ball', rules)
```

#### Using VS Code

1. Install "Python" extension
2. Add launch configuration:
   ```json
   {
     "type": "python",
     "request": "launch",
     "name": "Debug Tests",
     "module": "pytest",
     "args": ["tests/test_engine.py", "-v"]
   }
   ```

### Troubleshooting

#### Build Errors

**Problem**: `maturin develop` fails with "could not compile"

**Solution**:
```bash
# Clean and rebuild
cargo clean
maturin develop
```

**Problem**: Import error after rebuild

**Solution**:
```bash
# Ensure virtual environment is active
source .venv/bin/activate
# Reinstall
maturin develop
```

#### Test Failures

**Problem**: Tests pass locally but fail in CI

**Solution**:
- Check Python version matches CI
- Ensure all dependencies are in `pyproject.toml`
- Check for platform-specific code

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          components: clippy, rustfmt
      
      - name: Rust format check
        run: cargo fmt --check
      
      - name: Rust lint
        run: cargo clippy -- -D warnings
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Python lint
        run: |
          pip install ruff mypy
          ruff check .
          mypy baselom_core

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install maturin pytest pytest-cov
          maturin develop
      
      - name: Rust tests
        run: cargo test
      
      - name: Python tests
        run: pytest --cov=baselom_core --cov-fail-under=90

  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Build wheel
        run: |
          pip install maturin
          maturin build --release
      
      - name: Upload wheel
        uses: actions/upload-artifact@v3
        with:
          name: wheels-${{ matrix.os }}
          path: target/wheels/*.whl
```

## Release Process

### Version Bumping

1. Update version in `Cargo.toml`:
   ```toml
   [package]
   version = "0.2.0"
   ```

2. Update version in `pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"
   ```

3. Update `CHANGELOG.md`

4. Create tag:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

### Publishing

```bash
# Build wheels for all platforms (via CI)
# Then publish to PyPI
maturin publish

# Or via twine
twine upload target/wheels/*.whl
```

## Code Style Guide

### Rust Style

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `cargo fmt` for formatting
- Use `cargo clippy` for linting
- Document all public items with `///` comments

```rust
/// Applies a pitch result to the game state.
///
/// # Arguments
///
/// * `state` - Current game state
/// * `pitch` - The pitch result
/// * `rules` - Game rules configuration
///
/// # Returns
///
/// Tuple of (new state, event) or error
///
/// # Examples
///
/// ```
/// let (new_state, event) = apply_pitch(&state, PitchResult::Ball, &rules)?;
/// ```
pub fn apply_pitch(
    state: &GameState,
    pitch: PitchResult,
    rules: &GameRules,
) -> Result<(GameState, Event), BaselomError> {
    // Implementation
}
```

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints everywhere
- Document with docstrings (Google style)

```python
def apply_pitch(
    state: GameState,
    pitch_result: str,
    rules: GameRules,
) -> tuple[GameState, Event]:
    """Apply a pitch result to the game state.

    Args:
        state: Current game state.
        pitch_result: The pitch outcome ('ball', 'strike', etc.).
        rules: Game rules configuration.

    Returns:
        Tuple of (new_state, event).

    Raises:
        ValidationError: If inputs are invalid.
        StateError: If game has ended.

    Example:
        >>> new_state, event = apply_pitch(state, 'ball', rules)
        >>> assert new_state.balls == state.balls + 1
    """
    # Implementation
```

## See Also

- [Architecture](./architecture.md) - System design
- [Testing](./testing.md) - Test strategy
- [API Reference](./api-reference.md) - Public API
- [Versioning](./versioning.md) - Version policy
