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

- **[Architecture](./architecture.md)** - System architecture, Rust/Python hybrid design
- **[Data Models](./data-models.md)** - GameState, GameRules, Event specifications
- **[API Reference](./api-reference.md)** - Public function specifications

### Rules & Logic

- **[Rules Logic](./rules-logic.md)** - Baseball rule processing specifications

### Technical

- **[Serialization](./serialization.md)** - JSON serialization/deserialization
- **[Error Handling](./error-handling.md)** - Exception specifications

### Development

- **[Testing](./testing.md)** - Test strategy and required test cases
- **[Development Guide](./development.md)** - Setup, build, CI/CD
- **[Versioning](./versioning.md)** - Version policy and compatibility

## Quick Links

- [GitHub Repository](https://github.com/tohboeh5/baselom)
- [README](../README.md)

---

*Version: v0.1.0 (Draft)*
