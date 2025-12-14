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
| Rust core (statistics) | ≥95% |
| Rust core (roster) | ≥95% |
| Rust core (archive) | ≥95% |
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
        """apply_pitch should complete in under 100μs (target from architecture.md)."""
        state = create_valid_state()
        
        result = benchmark(lambda: apply_pitch(state, 'ball', rules))
        
        assert result.stats.mean < 0.0001  # 100μs
    
    def test_full_game_simulation(self, benchmark):
        """Full 9-inning game should simulate in under 50ms (target from architecture.md)."""
        def simulate_game():
            state = initial_game_state(...)
            while state.game_status != 'final':
                state, _ = apply_random_pitch(state, rules)
            return state
        
        result = benchmark(simulate_game)
        
        assert result.stats.mean < 0.05  # 50ms
```

### 7. Statistics Tests

```python
class TestStatistics:
    def test_batting_average_calculation(self):
        """Batting average should be hits / at_bats."""
        avg = calculate_batting_average(hits=30, at_bats=100)
        assert avg == 0.300
    
    def test_batting_average_zero_at_bats(self):
        """Batting average with zero at_bats should return 0."""
        avg = calculate_batting_average(hits=0, at_bats=0)
        assert avg == 0.0
    
    def test_era_calculation(self):
        """ERA should be (earned_runs * 9) / innings_pitched."""
        era = calculate_era(earned_runs=27, innings_pitched=81.0)
        assert era == 3.0
    
    def test_ops_calculation(self):
        """OPS should be OBP + SLG."""
        stats = PlayerBattingStats(
            player_id='test',
            at_bats=100,
            hits=30,
            singles=20,
            doubles=5,
            triples=2,
            home_runs=3,
            walks=10
        )
        # OBP = (30 + 10) / (100 + 10) = 0.364
        # SLG = (20 + 10 + 6 + 12) / 100 = 0.48
        assert abs(stats.ops - 0.844) < 0.01
    
    def test_aggregate_stats_across_games(self):
        """Stats should aggregate correctly across multiple games."""
        game1_stats = create_game_stats(hits=2, at_bats=4)
        game2_stats = create_game_stats(hits=1, at_bats=3)
        
        season = aggregate_stats('player_1', [game1_stats, game2_stats])
        
        assert season.batting.hits == 3
        assert season.batting.at_bats == 7
        assert season.games_played == 2
```

### 8. Roster Management Tests

```python
class TestRosterManagement:
    def test_create_roster(self):
        """Should create roster with all players active."""
        players = [Player(player_id=f'p{i}', name=f'Player {i}') 
                   for i in range(25)]
        roster = create_roster('team_1', 'Test Team', players)
        
        assert len(roster.players) == 25
        assert all(p.status == PlayerStatus.ACTIVE for p in roster.players)
    
    def test_update_player_status(self):
        """Should update player status correctly."""
        roster = create_test_roster()
        updated = update_player_status(roster, 'p1', PlayerStatus.INJURED)
        
        entry = updated.get_player('p1')
        assert entry.status == PlayerStatus.INJURED
    
    def test_get_active_players(self):
        """Should return only active and bench players."""
        roster = create_roster_with_mixed_statuses()
        active = roster.get_active_players()
        
        assert all(p.status in (PlayerStatus.ACTIVE, PlayerStatus.BENCH) 
                   for p in active)
    
    def test_substitution_record(self):
        """Should record substitution correctly."""
        state = create_valid_state()
        request = create_substitution_request('p1', 'p2')
        state, event = force_substitution(state, request, rules)
        
        assert event.event_type == 'substitution'
        assert event.details['player_out'] == 'p1'
        assert event.details['player_in'] == 'p2'
```

### 9. Multi-Game Archive Tests

```python
class TestMultiGameArchive:
    def test_create_empty_archive(self):
        """Should create empty archive."""
        archive = create_game_archive('test', 'Test Archive')
        
        assert archive.archive_id == 'test'
        assert len(archive.games) == 0
    
    def test_add_game_to_archive(self):
        """Should add game to archive."""
        archive = create_game_archive('test', 'Test')
        final_state = create_finished_game_state()
        events = list(final_state.event_history)
        home_roster = create_test_roster('home')
        away_roster = create_test_roster('away')
        
        updated = add_game_to_archive(
            archive, final_state, events, home_roster, away_roster
        )
        
        assert len(updated.games) == 1
    
    def test_reject_incomplete_game(self):
        """Should reject game not in final status."""
        archive = create_game_archive('test', 'Test')
        in_progress_state = create_state(game_status='in_progress')
        
        with pytest.raises(ValidationError):
            add_game_to_archive(archive, in_progress_state, [], None, None)
    
    def test_export_import_roundtrip(self):
        """Archive should survive export/import."""
        archive = create_populated_archive()
        
        exported = export_archive(archive)
        imported = import_archive(exported)
        
        assert imported.archive_id == archive.archive_id
        assert len(imported.games) == len(archive.games)
    
    def test_query_by_team(self):
        """Should filter games by team."""
        archive = create_archive_with_multiple_teams()
        
        games = query_archive(archive, team_id='tigers')
        
        assert all(g.home_team == 'tigers' or g.away_team == 'tigers' 
                   for g in games)
    
    def test_query_by_date_range(self):
        """Should filter games by date range."""
        archive = create_archive_with_date_range()
        
        games = query_archive(
            archive, 
            start_date='2024-06-01', 
            end_date='2024-06-30'
        )
        
        assert all('2024-06' in g.date for g in games)
```

### 10. Serialization Tests

```python
class TestSerialization:
    def test_canonical_json_determinism(self):
        """canonical_json_bytes should produce identical output for same input."""
        payload = {
            'batter_id': 'player_1',
            'pitcher_id': 'player_2',
            'inning': 5,
            'top': True
        }
        
        result1 = canonical_json_bytes(payload)
        result2 = canonical_json_bytes(payload)
        
        assert result1 == result2
    
    def test_canonical_json_key_ordering(self):
        """Keys should be sorted lexicographically."""
        payload = {'zebra': 1, 'apple': 2, 'banana': 3}
        result = canonical_json_bytes(payload)
        
        # Keys should appear in order: apple, banana, zebra
        assert result == b'{"apple":2,"banana":3,"zebra":1}'
    
    def test_canonical_json_no_whitespace(self):
        """Canonical JSON should have no whitespace."""
        payload = {'key': 'value', 'number': 42}
        result = canonical_json_bytes(payload)
        
        assert b' ' not in result
        assert b'\n' not in result
    
    def test_event_id_excludes_timestamp(self):
        """event_id should be identical regardless of created_at."""
        payload = {'batter_id': 'p1', 'inning': 1, 'top': True}
        
        id1 = generate_event_id(payload, 'hit.v1', '1')
        id2 = generate_event_id(payload, 'hit.v1', '1')
        
        # Same payload = same ID
        assert id1 == id2
    
    def test_event_id_changes_with_schema_version(self):
        """Different schema versions should produce different event_ids."""
        payload = {'batter_id': 'p1', 'inning': 1, 'top': True}
        
        id_v1 = generate_event_id(payload, 'hit.v1', '1')
        id_v2 = generate_event_id(payload, 'hit.v1', '2')
        
        assert id_v1 != id_v2
    
    def test_state_hash_ignores_timestamps(self):
        """State hashes should be equal when only timestamps differ."""
        state1 = {'inning': 1, 'outs': 0, 'created_at': '2024-01-01T10:00:00Z'}
        state2 = {'inning': 1, 'outs': 0, 'created_at': '2024-01-02T15:30:00Z'}
        
        assert states_equal_ignoring_time(state1, state2)
    
    def test_state_hash_detects_differences(self):
        """State hashes should differ when game state differs."""
        state1 = {'inning': 1, 'outs': 0, 'created_at': '2024-01-01T10:00:00Z'}
        state2 = {'inning': 1, 'outs': 1, 'created_at': '2024-01-01T10:00:00Z'}
        
        assert not states_equal_ignoring_time(state1, state2)
```

### 11. Cross-Platform Interoperability Tests

```python
class TestCrossplatformInterop:
    """Tests to ensure Python and Rust produce identical serialization."""
    
    def test_python_rust_canonical_json_match(self):
        """Python and Rust should produce identical canonical JSON."""
        payload = {
            'game_id': 'test-game',
            'inning': 3,
            'top': False,
            'batter_id': 'player_42',
            'pitcher_id': 'player_17'
        }
        
        python_bytes = canonical_json_bytes(payload)
        rust_bytes = rust_canonical_json_bytes(payload)  # Via PyO3
        
        assert python_bytes == rust_bytes
    
    def test_python_rust_event_id_match(self):
        """Python and Rust should generate identical event_ids."""
        payload = {'game_id': 'g1', 'inning': 1, 'top': True}
        
        python_id = generate_event_id(payload, 'hit.v1', '1')
        rust_id = rust_generate_event_id(payload, 'hit.v1', '1')  # Via PyO3
        
        assert python_id == rust_id
    
    def test_state_serialization_roundtrip(self):
        """State should survive Python -> Rust -> Python roundtrip."""
        original = create_valid_state()
        
        # Serialize in Python
        python_json = serialize_state(original)
        
        # Process in Rust and back
        rust_processed = rust_process_state(python_json)
        
        # Deserialize back in Python
        restored = deserialize_state(rust_processed)
        
        assert states_equal_ignoring_time(
            serialize_state(original),
            serialize_state(restored)
        )
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py

@pytest.fixture
def default_rules():
    return GameRules()

@pytest.fixture
def pro_rules():
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
│       ├── pro_rules.json
│       └── youth_rules.json
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
