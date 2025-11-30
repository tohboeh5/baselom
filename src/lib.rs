//! Baselom Core - A lightweight, pure game-state engine for baseball.
//!
//! This crate implements inning progression, base/runner state, scoring,
//! and substitutions as an immutable, testable Finite State Machine (FSM).
//!
//! # Platform Support
//!
//! The core engine is designed to be platform-agnostic with conditional
//! bindings for different targets:
//!
//! - **Python** (v0.1.0): Via PyO3/maturin - `--features python`
//! - **WASM** (v0.2.0+): Via wasm-bindgen - `--features wasm`
//! - **Native**: Pure Rust library - default features
//!
//! # Architecture
//!
//! The core follows WASM-first design principles:
//! - No I/O or system calls
//! - Pure functions for state transitions
//! - Serialization-based communication (JSON)
//!
//! See `docs/architecture.md` for detailed design documentation.

// Platform-specific imports
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

// Core modules (platform-agnostic)
pub mod engine;
pub mod errors;
pub mod models;
pub mod validators;

// Re-export core types for convenience
pub use errors::BaselomError;
pub use models::{GameRules, GameState, Score};
pub use validators::validate_state;

// =============================================================================
// Python Bindings (feature = "python")
// =============================================================================

/// Python module entry point via PyO3.
#[cfg(feature = "python")]
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

// =============================================================================
// WASM Bindings (feature = "wasm") - Planned for v0.2.0
// =============================================================================

/// WASM module initialization.
/// This will be expanded in v0.2.0 with full game state bindings.
#[cfg(feature = "wasm")]
#[wasm_bindgen(start)]
pub fn wasm_init() {
    // Future: Initialize WASM module, set up panic hook, etc.
}

/// Get the library version (WASM).
#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
