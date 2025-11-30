# Testing

## Overview

This document defines the testing strategy, test categories, and required test cases for Baselom Core. The target is >90% code coverage with comprehensive scenario testing.

## Testing Strategy

### Test Pyramid

```
                    ┌─────────────────┐
                    │   End-to-End    │  ← Full game simulations
                    │     Tests       │
                    └────────┬────────┘
               ┌─────────────┴─────────────┐
               │    Integration Tests      │  ← Python/Rust boundary
               └─────────────┬─────────────┘
          ┌──────────────────┴──────────────────┐
          │           Unit Tests                 │  ← Individual functions
          └──────────────────────────────────────┘
```

### Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Rust core (models) | ≥95% |
| Rust core (engine) | ≥95% |
| Python wrappers | ≥90% |
| Serialization | ≥95% |
| Overall | ≥90% |

## Test Categories

### 1. Unit Tests

Test individual functions in isolation.

#### State Creation Tests

```python
class TestInitialGameState:
    def test_creates_valid_initial_state(self):
        state = initial_game_state(
            home_lineup=['h1'...'h9'],
            away_lineup=['a1'...'a9'],
            rules=GameRules()
        )
        assert state.inning == 1
        assert state.top == True
        assert state.outs == 0
        assert state.bases == (None, None, None)
        assert state.score == {'home': 0, 'away': 0}
    
    def test_rejects_invalid_lineup_size(self):
        with pytest.raises(ValidationError):
            initial_game_state(
                home_lineup=['h1', 'h2'],  # Too few
                away_lineup=['a1'...'a9'],
                rules=GameRules()
            )
    
    def test_rejects_duplicate_players(self):
        with pytest.raises(ValidationError):
            initial_game_state(
                home_lineup=['h1', 'h1', 'h3'...'h9'],  # Duplicate
                away_lineup=['a1'...'a9'],
                rules=GameRules()
            )
```

#### Count Processing Tests

```python
class TestCountProcessing:
    def test_ball_increments_count(self):
        state = create_state_with_count(balls=0, strikes=0)
        new_state, event = apply_pitch(state, 'ball', rules)
        assert new_state.balls == 1
        assert new_state.strikes == 0
    
    def test_fourth_ball_is_walk(self):
        state = create_state_with_count(balls=3, strikes=0)
        new_state, event = apply_pitch(state, 'ball', rules)
        assert event.event_type == 'walk'
        assert new_state.bases[0] == state.current_batter_id
    
    def test_strike_increments_count(self):
        state = create_state_with_count(balls=0, strikes=0)
        new_state, event = apply_pitch(state, 'strike_called', rules)
        assert new_state.balls == 0
        assert new_state.strikes == 1
    
    def test_third_strike_is_strikeout(self):
        state = create_state_with_count(balls=0, strikes=2)
        new_state, event = apply_pitch(state, 'strike_swinging', rules)
        assert event.event_type == 'strikeout_swinging'
        assert new_state.outs == state.outs + 1
    
    def test_foul_with_two_strikes_no_change(self):
        state = create_state_with_count(balls=1, strikes=2)
        new_state, event = apply_pitch(state, 'foul', rules)
        assert new_state.balls == 1
        assert new_state.strikes == 2
    
    def test_foul_with_less_than_two_strikes_increments(self):
        state = create_state_with_count(balls=0, strikes=1)
        new_state, event = apply_pitch(state, 'foul', rules)
        assert new_state.strikes == 2
```

#### Hit Processing Tests

```python
class TestHitProcessing:
    def test_single_puts_batter_on_first(self):
        state = create_state_with_empty_bases()
        new_state, event = apply_pitch(
            state, 'in_play', rules, 
            batted_ball_result='single'
        )
        assert new_state.bases[0] == state.current_batter_id
        assert event.event_type == 'single'
    
    def test_single_advances_runner_from_second(self):
        state = create_state_with_runner_on_second('runner_1')
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='single'
        )
        # Runner can score or go to third
        assert 'runner_1' not in [new_state.bases[1], new_state.bases[0]]
    
    def test_home_run_clears_bases_and_scores_all(self):
        state = create_state_with_bases_loaded()
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='home_run'
        )
        assert new_state.bases == (None, None, None)
        assert event.rbi == 4  # 3 runners + batter
    
    def test_double_puts_batter_on_second(self):
        state = create_state_with_empty_bases()
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='double'
        )
        assert new_state.bases[1] == state.current_batter_id
```

#### Out Processing Tests

```python
class TestOutProcessing:
    def test_ground_out_increments_outs(self):
        state = create_state_with_outs(0)
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='ground_out'
        )
        assert new_state.outs == 1
    
    def test_third_out_ends_half_inning(self):
        state = create_state_with_outs(2)
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='fly_out'
        )
        assert new_state.outs == 0  # Reset
        assert new_state.top != state.top  # Flipped
    
    def test_double_play_adds_two_outs(self):
        state = create_state_with_runner_on_first_and_outs(0)
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='double_play'
        )
        assert new_state.outs == 2
```

### 2. Integration Tests

Test Python-Rust boundary and component interaction.

```python
class TestPythonRustIntegration:
    def test_state_roundtrip_serialization(self):
        original = initial_game_state(...)
        serialized = serialize_state(original)
        restored = deserialize_state(serialized)
        assert restored == original
    
    def test_multiple_pitch_sequence(self):
        state = initial_game_state(...)
        
        # Ball
        state, _ = apply_pitch(state, 'ball', rules)
        # Strike
        state, _ = apply_pitch(state, 'strike_called', rules)
        # Ball
        state, _ = apply_pitch(state, 'ball', rules)
        # Single
        state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='single'
        )
        
        assert event.event_type == 'single'
        assert len(state.event_history) == 4
    
    def test_rust_error_converts_to_python_exception(self):
        state = create_invalid_state()
        with pytest.raises(ValidationError):
            validate_state(state)
```

### 3. Scenario Tests

Test realistic game scenarios.

```python
class TestGameScenarios:
    def test_bases_loaded_walk_scores_run(self):
        """Bases loaded walk should score runner from third."""
        state = create_state_with_bases_loaded_and_full_count()
        
        new_state, event = apply_pitch(state, 'ball', rules)
        
        assert event.event_type == 'walk'
        assert new_state.score[new_state.batting_team] == state.score[state.batting_team] + 1
        assert new_state.bases[2] is not None  # New runner on third
    
    def test_walkoff_home_run(self):
        """Home run in bottom of 9th with tie should end game."""
        state = create_state(
            inning=9,
            top=False,
            score={'home': 3, 'away': 3}
        )
        
        new_state, event = apply_pitch(
            state, 'in_play', rules,
            batted_ball_result='home_run'
        )
        
        assert new_state.game_status == 'final'
        assert new_state.score['home'] == 4
        game_ended, winner = check_game_end(new_state, rules)
        assert game_ended
        assert winner == 'home'
    
    def test_three_strikeouts_end_inning(self):
        """Three strikeouts should end the half-inning."""
        state = create_state(inning=1, top=True, outs=0)
        
        # First strikeout
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        assert state.outs == 1
        
        # Second strikeout
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        assert state.outs == 2
        
        # Third strikeout
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, _ = apply_pitch(state, 'strike_swinging', rules)
        state, event = apply_pitch(state, 'strike_swinging', rules)
        
        assert state.top == False  # Now bottom of 1st
        assert state.outs == 0
```

### 4. Edge Case Tests

```python
class TestEdgeCases:
    def test_extra_innings_with_tiebreaker_rule(self):
        """Extra innings should place runner on second."""
        rules = GameRules(extra_innings_tiebreaker='runner_on_second')
        state = create_state(inning=10, top=True)
        
        # After inning transition
        assert state.bases[1] is not None  # Runner on 2nd
    
    def test_mercy_rule_triggers_game_end(self):
        """Large lead should trigger mercy rule."""
        rules = GameRules(
            mercy_rule_enabled=True,
            mercy_rule_threshold=10,
            mercy_rule_min_inning=5
        )
        state = create_state(
            inning=5,
            score={'home': 15, 'away': 3}
        )
        
        game_ended, winner = check_game_end(state, rules)
        assert game_ended
        assert winner == 'home'
    
    def test_foul_tip_with_two_strikes_is_strikeout(self):
        """Foul tip caught with two strikes is strikeout."""
        state = create_state_with_count(balls=2, strikes=2)
        
        new_state, event = apply_pitch(state, 'foul_tip', rules)
        
        assert event.event_type == 'strikeout'
        assert new_state.outs == state.outs + 1
    
    def test_maximum_inning_limit(self):
        """Game should end at maximum innings."""
        rules = GameRules(max_innings=9, max_extra_innings=2)
        state = create_state(inning=12)  # 9 + 2 extra exceeded
        
        game_ended, _ = check_game_end(state, rules)
        assert game_ended
```

### 5. Validation Tests

```python
class TestValidation:
    def test_validate_correct_state(self):
        state = create_valid_state()
        result = validate_state(state)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_invalid_outs(self):
        state = create_state_with_invalid_outs(5)
        result = validate_state(state)
        assert not result.is_valid
        assert 'outs' in str(result.errors)
    
    def test_validate_negative_score(self):
        state = create_state_with_score({'home': -1, 'away': 0})
        result = validate_state(state)
        assert not result.is_valid
    
    def test_validate_duplicate_runners(self):
        state = create_state_with_bases(('player_1', 'player_1', None))
        result = validate_state(state)
        assert not result.is_valid
```

### 6. Performance Tests

```python
class TestPerformance:
    def test_apply_pitch_latency(self, benchmark):
        """apply_pitch should complete in under 1μs."""
        state = create_valid_state()
        
        result = benchmark(lambda: apply_pitch(state, 'ball', rules))
        
        assert result.stats.mean < 0.000001  # 1μs
    
    def test_full_game_simulation(self, benchmark):
        """Full 9-inning game should simulate in under 1ms."""
        def simulate_game():
            state = initial_game_state(...)
            while state.game_status != 'final':
                state, _ = apply_random_pitch(state, rules)
            return state
        
        result = benchmark(simulate_game)
        
        assert result.stats.mean < 0.001  # 1ms
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py

@pytest.fixture
def default_rules():
    return GameRules()

@pytest.fixture
def mlb_rules():
    return GameRules(
        designated_hitter=True,
        extra_innings_tiebreaker='runner_on_second'
    )

@pytest.fixture
def initial_state(default_rules):
    return initial_game_state(
        home_lineup=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9'],
        away_lineup=['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9'],
        rules=default_rules
    )

@pytest.fixture
def bases_loaded_state(initial_state):
    return initial_state._replace(
        bases=('runner_1', 'runner_2', 'runner_3')
    )

@pytest.fixture
def two_outs_state(initial_state):
    return initial_state._replace(outs=2)
```

### State Builders

```python
# test_utils.py

class GameStateBuilder:
    """Fluent builder for test game states."""
    
    def __init__(self):
        self._state = {
            'inning': 1,
            'top': True,
            'outs': 0,
            'balls': 0,
            'strikes': 0,
            'bases': (None, None, None),
            'score': {'home': 0, 'away': 0},
            ...
        }
    
    def with_inning(self, inning: int, top: bool = True):
        self._state['inning'] = inning
        self._state['top'] = top
        return self
    
    def with_count(self, balls: int, strikes: int):
        self._state['balls'] = balls
        self._state['strikes'] = strikes
        return self
    
    def with_bases(self, first=None, second=None, third=None):
        self._state['bases'] = (first, second, third)
        return self
    
    def with_outs(self, outs: int):
        self._state['outs'] = outs
        return self
    
    def build(self) -> GameState:
        return GameState(**self._state)

# Usage
state = (GameStateBuilder()
    .with_inning(5, top=False)
    .with_count(2, 2)
    .with_bases(first='r1', third='r3')
    .with_outs(1)
    .build())
```

## Running Tests

### Python Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=baselom_core --cov-report=html

# Specific test file
pytest tests/test_engine.py

# Specific test class
pytest tests/test_engine.py::TestCountProcessing

# Specific test
pytest tests/test_engine.py::TestCountProcessing::test_ball_increments_count

# Performance tests
pytest tests/test_performance.py --benchmark-only
```

### Rust Tests

```bash
# All tests
cargo test

# With output
cargo test -- --nocapture

# Specific test
cargo test test_apply_pitch

# Benchmarks
cargo bench
```

### CI Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install maturin pytest pytest-cov
          maturin develop
      
      - name: Run Rust tests
        run: cargo test
      
      - name: Run Python tests
        run: pytest --cov=baselom_core --cov-fail-under=90
```

## Test Data Management

### Fixtures Directory

```
tests/
├── fixtures/
│   ├── states/
│   │   ├── initial_state.json
│   │   ├── bases_loaded.json
│   │   └── ninth_inning_tie.json
│   ├── events/
│   │   ├── single.json
│   │   └── home_run.json
│   └── rules/
│       ├── mlb_rules.json
│       └── little_league_rules.json
└── test_*.py
```

### Loading Fixtures

```python
@pytest.fixture
def fixture_loader():
    def _load(path: str) -> dict:
        fixture_path = Path(__file__).parent / 'fixtures' / path
        return json.loads(fixture_path.read_text())
    return _load

def test_scenario(fixture_loader):
    state_data = fixture_loader('states/bases_loaded.json')
    state = deserialize_state(state_data)
    # Test with loaded state
```

## See Also

- [Development Guide](./development.md) - Setup and CI details
- [API Reference](./api-reference.md) - Function specifications
- [Error Handling](./error-handling.md) - Testing error conditions
