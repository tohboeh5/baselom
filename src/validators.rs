//! State validation rules.

use crate::errors::BaselomError;
use crate::models::GameState;

/// Validate that a game state is consistent.
pub fn validate_state(state: &GameState) -> Result<(), BaselomError> {
    // Validate outs (u8 type guarantees non-negative, so only check upper bound)
    if state.outs > 2 {
        return Err(BaselomError::ValidationError(
            "Outs must be between 0 and 2".to_string(),
        ));
    }

    // Validate inning (u8 type guarantees non-negative, so only check for zero)
    if state.inning == 0 {
        return Err(BaselomError::ValidationError(
            "Inning must be at least 1".to_string(),
        ));
    }

    Ok(())
}
