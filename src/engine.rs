//! FSM engine logic for state transitions.

use crate::errors::BaselomError;
use crate::models::{GameRules, GameState};

const FIRST_BASE: usize = 0;
const SECOND_BASE: usize = 1;
const THIRD_BASE: usize = 2;

/// Apply a pitch result to the game state.
pub fn apply_pitch(
    state: &GameState,
    pitch_result: &str,
    _rules: &GameRules,
) -> Result<GameState, BaselomError> {
    match pitch_result {
        "ball" => {
            if state.balls < 3 {
                Ok(GameState {
                    balls: state.balls + 1,
                    ..state.clone()
                })
            } else {
                Ok(process_walk(state))
            }
        }
        "strike_called" | "strike_swinging" => {
            if state.strikes < 2 {
                Ok(GameState {
                    strikes: state.strikes + 1,
                    ..state.clone()
                })
            } else {
                Ok(record_out(state))
            }
        }
        "foul" => {
            if state.strikes < 2 {
                Ok(GameState {
                    strikes: state.strikes + 1,
                    ..state.clone()
                })
            } else {
                Ok(state.clone())
            }
        }
        "foul_tip" => {
            if state.strikes >= 2 {
                Ok(record_out(state))
            } else {
                Ok(GameState {
                    strikes: state.strikes + 1,
                    ..state.clone()
                })
            }
        }
        other => Err(BaselomError::ValidationError(format!(
            "invalid pitch_result '{other}'"
        ))),
    }
}

fn record_out(state: &GameState) -> GameState {
    let mut outs = state.outs + 1;
    let mut top = state.top;
    let mut inning = state.inning;
    let mut bases = state.bases.clone();

    if outs >= 3 {
        outs = 0;
        bases = (None, None, None);
        if state.top {
            top = false;
        } else {
            top = true;
            inning = state.inning + 1;
        }
    }

    GameState {
        outs,
        balls: 0,
        strikes: 0,
        bases,
        top,
        inning,
        ..state.clone()
    }
}

fn process_walk(state: &GameState) -> GameState {
    let mut bases = [
        state.bases.0.clone(),
        state.bases.1.clone(),
        state.bases.2.clone(),
    ];
    let mut incoming = state.current_batter_id.clone();
    let mut runs_scored = 0u32;

    for base_index in [FIRST_BASE, SECOND_BASE, THIRD_BASE] {
        if incoming.is_none() {
            break;
        }

        if bases[base_index].is_none() {
            bases[base_index] = incoming.clone();
            incoming = None;
        } else {
            let displaced = bases[base_index].clone();
            bases[base_index] = incoming.clone();
            incoming = displaced;
        }
    }

    if incoming.is_some() {
        runs_scored += 1;
    }

    let mut score = state.score.clone();
    if runs_scored > 0 {
        if state.top {
            score.away += runs_scored;
        } else {
            score.home += runs_scored;
        }
    }

    GameState {
        balls: 0,
        strikes: 0,
        bases: (
            bases[FIRST_BASE].clone(),
            bases[SECOND_BASE].clone(),
            bases[THIRD_BASE].clone(),
        ),
        score,
        ..state.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn base_state() -> GameState {
        GameState {
            current_batter_id: Some("b1".to_string()),
            current_pitcher_id: Some("p1".to_string()),
            ..GameState::default()
        }
    }

    #[test]
    fn test_ball_increments_count() {
        let state = base_state();
        let rules = GameRules::default();
        let result = apply_pitch(&state, "ball", &rules).unwrap();
        assert_eq!(result.balls, 1);
        assert_eq!(result.strikes, 0);
    }

    #[test]
    fn test_strikeout_adds_out() {
        let state = GameState {
            strikes: 2,
            ..base_state()
        };
        let rules = GameRules::default();
        let result = apply_pitch(&state, "strike_swinging", &rules).unwrap();
        assert_eq!(result.outs, 1);
        assert_eq!(result.balls, 0);
        assert_eq!(result.strikes, 0);
    }
}
