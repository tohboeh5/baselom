# Baselom Core - Copilot Instructions

## Code Quality Requirements

**IMPORTANT**: Always run lint, format, and test commands before committing any changes.

### Required Commands

Before every commit or PR, run these commands:

```bash
# Format all code (Rust + Python)
mise run format

# Lint all code (Rust + Python)
mise run lint

# Run all tests (Rust + Python + WASM check)
mise run test
```

### Individual Commands

For targeted checks:

```bash
# Rust only
mise run format-rust
mise run lint-rust
mise run test-rust

# Python only
mise run format-python
mise run lint-python
mise run test-python

# WASM check
mise run test-wasm
```

### Pre-commit Hooks

Pre-commit hooks are configured to run `format` and `lint` automatically on every commit.
Make sure pre-commit is installed:

```bash
pre-commit install
```

### CI/CD

GitHub Actions automatically runs on every push and PR:
- `mise run lint` - Format and lint check
- `mise run test` - All tests (Rust + Python + WASM)

### Guidelines

1. **Always format before committing**: Use `mise run format` to ensure consistent code style
2. **Always lint before committing**: Use `mise run lint` to catch issues early
3. **Always test before pushing**: Use `mise run test` to verify all tests pass
4. **Fix lint errors immediately**: Don't ignore lint warnings or errors
5. **Keep tests passing**: Never push code that breaks existing tests

### Build Commands

```bash
# Build for development (Python bindings)
mise run build

# Build for release
mise run build-release

# Build WASM target
mise run build-wasm

# Check all targets compile
mise run check-all
```
