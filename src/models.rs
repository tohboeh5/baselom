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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_score_default() {
        let score = Score::default();
        assert_eq!(score.home, 0);
        assert_eq!(score.away, 0);
    }

    #[test]
    fn test_score_custom() {
        let score = Score { home: 3, away: 2 };
        assert_eq!(score.home, 3);
        assert_eq!(score.away, 2);
    }

    #[test]
    fn test_game_rules_default() {
        let rules = GameRules::default();
        assert!(!rules.designated_hitter);
        assert_eq!(rules.max_innings, Some(9));
        assert!(rules.extra_innings_tiebreaker.is_none());
    }

    #[test]
    fn test_game_rules_custom() {
        let rules = GameRules {
            designated_hitter: true,
            max_innings: Some(7),
            extra_innings_tiebreaker: Some("runner_on_second".to_string()),
        };
        assert!(rules.designated_hitter);
        assert_eq!(rules.max_innings, Some(7));
        assert_eq!(
            rules.extra_innings_tiebreaker,
            Some("runner_on_second".to_string())
        );
    }

    #[test]
    fn test_game_state_creation() {
        let state = GameState {
            inning: 1,
            top: true,
            outs: 0,
            bases: (None, None, None),
            score: Score::default(),
            current_batter_id: None,
            current_pitcher_id: None,
        };
        assert_eq!(state.inning, 1);
        assert!(state.top);
        assert_eq!(state.outs, 0);
    }

    #[test]
    fn test_score_serialization() {
        let score = Score { home: 5, away: 3 };
        let json = serde_json::to_string(&score).unwrap();
        let deserialized: Score = serde_json::from_str(&json).unwrap();
        assert_eq!(score, deserialized);
    }

    #[test]
    fn test_game_rules_serialization() {
        let rules = GameRules::default();
        let json = serde_json::to_string(&rules).unwrap();
        let deserialized: GameRules = serde_json::from_str(&json).unwrap();
        assert_eq!(rules, deserialized);
    }
}
