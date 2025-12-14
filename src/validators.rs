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

    if state.balls > 3 {
        return Err(BaselomError::ValidationError(
            "Balls must be between 0 and 3".to_string(),
        ));
    }

    if state.strikes > 2 {
        return Err(BaselomError::ValidationError(
            "Strikes must be between 0 and 2".to_string(),
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::Score;

    fn create_test_state(inning: u8, outs: u8) -> GameState {
        GameState {
            inning,
            top: true,
            outs,
            balls: 0,
            strikes: 0,
            bases: (None, None, None),
            score: Score::default(),
            current_batter_id: None,
            current_pitcher_id: None,
        }
    }

    #[test]
    fn test_valid_state() {
        let state = create_test_state(1, 0);
        assert!(validate_state(&state).is_ok());
    }

    #[test]
    fn test_valid_state_max_outs() {
        let state = create_test_state(1, 2);
        assert!(validate_state(&state).is_ok());
    }

    #[test]
    fn test_invalid_outs_too_many() {
        let state = create_test_state(1, 3);
        let result = validate_state(&state);
        assert!(result.is_err());
        assert!(matches!(result, Err(BaselomError::ValidationError(_))));
    }

    #[test]
    fn test_invalid_inning_zero() {
        let state = create_test_state(0, 0);
        let result = validate_state(&state);
        assert!(result.is_err());
        assert!(matches!(result, Err(BaselomError::ValidationError(_))));
    }

    #[test]
    fn test_valid_high_inning() {
        let state = create_test_state(15, 1);
        assert!(validate_state(&state).is_ok());
    }
}
