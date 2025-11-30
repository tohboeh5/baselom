//! Core data structures for the baseball game state.

use serde::{Deserialize, Serialize};

/// Represents the current state of a baseball game.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GameState {
    /// 1-based inning number
    pub inning: u8,
    /// True if top of inning (away team batting)
    pub top: bool,
    /// Number of outs (0-2)
    pub outs: u8,
    /// Base runners: (first, second, third)
    pub bases: (Option<String>, Option<String>, Option<String>),
    /// Current score
    pub score: Score,
    /// ID of current batter
    pub current_batter_id: Option<String>,
    /// ID of current pitcher
    pub current_pitcher_id: Option<String>,
}

/// Score tracking for both teams.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct Score {
    pub home: u32,
    pub away: u32,
}

/// Configurable game rules.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GameRules {
    /// Whether designated hitter is used
    pub designated_hitter: bool,
    /// Maximum number of innings (None for unlimited)
    pub max_innings: Option<u8>,
    /// Extra innings tiebreaker rule
    pub extra_innings_tiebreaker: Option<String>,
}

impl Default for GameRules {
    fn default() -> Self {
        Self {
            designated_hitter: false,
            max_innings: Some(9),
            extra_innings_tiebreaker: None,
        }
    }
}
