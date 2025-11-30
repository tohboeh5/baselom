//! Baselom Core - A lightweight, pure game-state engine for baseball.
//!
//! This crate implements inning progression, base/runner state, scoring,
//! and substitutions as an immutable, testable Finite State Machine (FSM).

#[cfg(feature = "python")]
use pyo3::prelude::*;

pub mod engine;
pub mod errors;
pub mod models;
pub mod validators;

/// A Python module implemented in Rust.
#[cfg(feature = "python")]
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
