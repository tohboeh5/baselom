# Specification Fixes Summary

This document summarizes the inconsistencies found in the Baselom Core specifications and the fixes applied.

## Issues Identified and Fixed

### Issue 1: Event/Result String Naming Inconsistency

**Problem**: README used `hit_single` as a pitch result, while api-reference.md correctly defines the two-step process of `in_play` pitch result + `batted_ball_result`.

**Location**: README.md Quick Start example

**Before**:
```python
state, event = apply_pitch(state, 'hit_single', rules)
print(event)
# {'type': 'single', 'batter': 'a1', 'rbi': 0, ...}
```

**After**:
```python
state, event = apply_pitch(state, 'in_play', rules, batted_ball_result='single')
print(event)
# {'event_type': 'single', 'batter_id': 'a1', 'rbi': 0, ...}
```

**Impact**: Users following README example would get errors. Fixed to match API specification.

---

### Issue 2: BaseIndex Type Inconsistency

**Problem**: `BaseIndex` type alias was defined as `Literal[0, 1, 2]` (first, second, third), but API functions used indices 0-3 where 3=home plate for runner advancement.

**Location**: docs/data-models.md Type Aliases section

**Fix**: Added new `BaseOrHome` type alias for contexts requiring home plate:

```python
BaseIndex: TypeAlias = Literal[0, 1, 2]
"""Base index for base state: 0=first, 1=second, 2=third."""

BaseOrHome: TypeAlias = Literal[0, 1, 2, 3]
"""Base index including home plate: 0=first, 1=second, 2=third, 3=home.
Used in runner advancement operations."""
```

**Impact**: Clarifies when home plate (3) is valid in API calls like `runner_advances`.

---

### Issue 3: no_std/WASM vs serde_json Contradiction

**Problem**: Architecture document claimed `#![no_std]` compatibility while listing `serde_json` as WASM-compatible. However, `serde_json` requires `std` by default.

**Location**: docs/architecture.md

**Fix**:
1. Updated section title from "No Standard Library Dependencies" to "Standard Library Conditional Usage"
2. Added documentation explaining that `serde_json` requires `std` feature
3. Updated dependencies table to show `serde_json` as "⚠️ Requires `std`"
4. Added `postcard` as a no_std alternative for binary serialization

**Impact**: Prevents confusion when building for no_std WASM targets.

---

### Issue 4: GameState Field Mismatches

**Problem**: README showed GameState with only 13 fields, missing `balls`, `strikes`, `lineups`, `pitchers`, `game_status`, and `created_at`. Also had incorrect type annotation for `event_history`.

**Location**: README.md Core Data Models section

**Fix**: Updated README GameState definition to include all 19 fields matching data-models.md:
- Added missing fields: `balls`, `strikes`, `lineups`, `pitchers`, `game_status`, `created_at`
- Fixed `batting_team`/`fielding_team` type from `str` to `Literal['home', 'away']`
- Fixed `event_history` type from `Tuple[dict, ...]` to `Tuple[Dict[str, Any], ...]`
- Added reference link to complete specification

**Impact**: Users get accurate picture of GameState structure from README.

---

### Issue 5: Serialization Specification Enhancements

**Problem**: Serialization spec lacked:
- JSON schema versioning details
- Forward/backward compatibility guarantees
- Event type discriminator documentation

**Location**: docs/serialization.md Versioning section

**Fix**: Expanded "Versioning and Compatibility" section to include:
- Distinction between `rules_version` and `baselom_version`
- JSON schema version documentation
- Compatibility guarantees table
- Forward/backward compatibility rules
- Event type discriminator pattern example

**Impact**: External system integrators have clear compatibility expectations.

---

### Issue 6: Error Handling Specification Enhancements

**Problem**: Error handling documentation lacked:
- PyO3 error mapping rules
- REST/HTTP error response format
- HTTP status code mapping

**Location**: docs/error-handling.md

**Fix**: Added comprehensive sections:
1. **PyO3 Error Mapping Rules Table**: Maps Rust error variants to Python exceptions
2. **Exception Details Preservation**: Shows how Rust error details become Python exception attributes
3. **REST/HTTP API Error Format**: JSON schema for error responses
4. **HTTP Status Code Mapping Table**: Maps error codes to HTTP status codes
5. **Example REST Error Response**: Complete JSON example
6. **Converting Exceptions to HTTP Responses**: Python code sample

**Impact**: Developers building REST APIs on top of Baselom have clear guidance.

---

### Issue 7: Game Status Enum Inconsistency

**Problem**: 
- GameStatus enum has 6 values
- GameState.game_status only allows 3 values
- Serialization schema showed 4 values

**Locations**: 
- docs/data-models.md (GameStatus enum and GameState definition)
- docs/serialization.md (JSON schema)

**Fix**:
1. Updated GameStatus enum with docstring explaining which values are used where
2. Added explicit note about valid GameState.game_status values
3. Fixed serialization.md JSON schema to only include 3 valid values
4. Added description explaining the discrepancy

**Impact**: Prevents validation errors from using wrong status values.

---

### Issue 8: Function Name Inconsistency

**Problem**: README listed `aggregate_season_stats()` while api-reference.md defines `aggregate_stats()`.

**Location**: README.md Statistics Functions table

**Fix**: Changed `aggregate_season_stats()` to `aggregate_stats()` to match API reference.

**Impact**: Users can find correct function in API documentation.

---

## Documents Modified

1. **README.md**
   - Fixed Quick Start example (Issue 1)
   - Updated GameState definition (Issue 4)
   - Fixed function name (Issue 8)

2. **docs/data-models.md**
   - Added BaseOrHome type alias (Issue 2)
   - Enhanced GameStatus enum documentation (Issue 7)

3. **docs/architecture.md**
   - Clarified no_std/std requirements (Issue 3)
   - Updated dependencies table (Issue 3)

4. **docs/serialization.md**
   - Fixed game_status enum values (Issue 7)
   - Enhanced versioning section (Issue 5)

5. **docs/error-handling.md**
   - Added PyO3 mapping rules (Issue 6)
   - Added REST error format (Issue 6)
   - Added HTTP status code mapping (Issue 6)

---

## Verification Checklist

- [x] All pitch result strings consistent across documents
- [x] Base index types clearly defined with home plate handling
- [x] no_std requirements accurately documented
- [x] GameState fields match between README and data-models
- [x] Serialization versioning fully documented
- [x] Error handling covers all integration scenarios
- [x] Game status values consistent across all documents
- [x] Function names match between README and API reference

---

*Document created: 2024*
*Specification version: v0.1.0 (Draft)*
