# Implementation Plan (TDD-Driven)

This plan translates the README and existing docs into a concrete, milestone-based roadmap. Each milestone is defined with **TDD-first deliverables**, required tests, and exit criteria. The focus is the v0.1.0 Python release while keeping WASM compatibility for v0.2.0.

## Guiding Principles

- **TDD first**: write failing tests before implementations; keep >90% coverage targets from [`testing.md`](./testing.md).
- **Immutable FSM**: preserve pure, side-effect-free transitions per [`architecture.md`](./architecture.md).
- **Content-addressed events**: deterministic serialization and event IDs per [`serialization.md`](./serialization.md).
- **Platform agnostic core**: no I/O in core logic; bindings isolated behind feature flags.
- **Incremental milestones**: each milestone produces releasable increments with CI green on `mise run format`, `mise run lint`, and `mise run test`.

## Milestones and TDD Scope

| # | Goal & Scope | Key Tests to Author First | Exit Criteria |
|---|--------------|---------------------------|---------------|
| **M1. Data Foundations** | Finalize `GameState`, `GameRules`, error types, and validators. Ensure builders/fixtures exist. | Unit tests for model invariants (outs range, lineup size/duplicates, score non-negative). Validation error mapping (Rust → Python). Serialization determinism smoke tests for models. | All validation/unit tests green; schemas stable; canonical JSON round-trip for models. |
| **M2. Pitch & Count Engine** | Implement pitch processing, count rules, walks/strikeouts, foul logic. | Unit tests mirroring `TestCountProcessing` examples; scenario test for three strikeouts ending half-inning; regression tests for foul-tip with two strikes. | Engine returns correct state/events across count edge cases; coverage ≥95% for engine module. |
| **M3. Batted Ball & Base Running** | Single/double/triple/HR handling, runner advancement rules, double plays, inning transitions. | Unit tests for singles/doubles/HR with runners; scenario test for bases-loaded walk scoring; double-play outs and inning flip tests. | Base runner logic deterministic; inning progression correct; event payloads include runner movement. |
| **M4. Event Sourcing & Serialization** | Event envelope/payload, SHA-256 content IDs, canonical JSON. | Tests for canonical JSON ordering/no whitespace; event_id stability across timestamps; state hash ignores timestamps; Python↔Rust canonical JSON parity tests. | Deterministic event_id generation; serialization tests green across Rust/Python boundary. |
| **M5. Python API Wrappers** | PyO3 exports and Python conveniences (`initial_game_state`, `apply_pitch`, `validate_state`). | Integration tests for Python↔Rust roundtrip, error conversion, multiple pitch sequence length/history; fixtures for common states. | Public Python API matches README examples; integration tests passing; docs examples executable. |
| **M6. Statistics Module** | Batting average/ERA/OPS, aggregation across games. | Unit tests for stats formulas (zero at-bats, OPS calc); aggregation across multiple games; guardrails on division-by-zero. | Statistics functions return documented values; ≥95% coverage for stats module. |
| **M7. Roster Management** | Player status, substitutions, active roster queries. | Tests for create/update roster, substitution recording, active player filtering. | Roster mutations remain immutable; substitution events emitted with correct payload. |
| **M8. Multi-Game Archive** | Archive create/add/export/import/query. | Tests for rejecting non-final games, export/import roundtrip, filters by team/date. | Archive operations deterministic; content-addressed event references preserved. |
| **M9. WASM Readiness (v0.2.0 prep)** | Validate feature flags, `no_std` path, wasm-bindgen glue stubs. | Build check for `wasm32-unknown-unknown` target; cross-platform serialization parity tests (JSON path under `std`). | WASM build succeeds in CI; Python/Rust/WASM canonical JSON alignment documented. |
| **M10. Performance & Release Gate** | Benchmarks for `apply_pitch`, validation, full-game sim. | Benchmark tests with thresholds from [`architecture.md`](./architecture.md#performance-considerations); monitor regression thresholds. | Benchmarks recorded with environment notes; thresholds met in Release build; release notes updated. |

## Iteration & Workflow

1. **Pick milestone** → derive user stories from README/API docs.
2. **Write tests first** in `tests/` (unit + scenario) using builders/fixtures; add Rust tests when logic resides there.
3. **Implement minimal code** to satisfy tests, preserving immutability and pure functions.
4. **Run** `mise run format && mise run lint && mise run test`; keep CI green before moving on.
5. **Document decisions** inline or in relevant docs; update API examples when behavior changes.

## Risk & Dependency Notes

- **Cross-language parity**: prioritize integration tests early (M4–M5) to prevent drift between Rust and Python.
- **Deterministic serialization**: any change touching events must add/adjust canonical JSON tests.
- **WASM constraints**: avoid `std`-only APIs in core; keep feature flags explicit to ease M9.
- **Performance regressions**: add benchmarks near completion of each milestone to catch hotspots before release.

## Acceptance for v0.1.0

- Milestones M1–M8 completed with tests; M9 build check passes (no feature regressions); M10 benchmarks recorded.
- README quick-start flows execute via Python bindings.
- Coverage targets met; CI (lint/test) clean.
