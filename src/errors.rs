//! Error types for the Baselom Core engine.

use thiserror::Error;

/// Main error type for Baselom operations.
#[derive(Error, Debug)]
pub enum BaselomError {
    /// Invalid input data
    #[error("Validation error: {0}")]
    ValidationError(String),

    /// Invalid state transition
    #[error("State error: {0}")]
    StateError(String),

    /// Rule constraint violated
    #[error("Rule violation: {0}")]
    RuleViolation(String),
}
