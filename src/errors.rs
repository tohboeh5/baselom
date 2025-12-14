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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validation_error_display() {
        let err = BaselomError::ValidationError("test error".to_string());
        assert_eq!(format!("{}", err), "Validation error: test error");
    }

    #[test]
    fn test_state_error_display() {
        let err = BaselomError::StateError("state error".to_string());
        assert_eq!(format!("{}", err), "State error: state error");
    }

    #[test]
    fn test_rule_violation_display() {
        let err = BaselomError::RuleViolation("rule violation".to_string());
        assert_eq!(format!("{}", err), "Rule violation: rule violation");
    }
}
