# Versioning

## Overview

Baselom Core follows [Semantic Versioning 2.0.0](https://semver.org/) (SemVer) for all releases. This document defines the versioning policy, compatibility guarantees, and migration guidelines.

## Version Types

Baselom uses **three distinct version identifiers**:

| Version | Location | Purpose |
|---------|----------|---------|
| **Library Version** (SemVer) | Package metadata, `__version__` | Baselom Core release version |
| **Event Schema Version** | Event envelope `schema_version` | Version of event payload structure |
| **Rules Version** | `GameState.rules_version` | Baseball rules variant (e.g., "2024 MLB rules") |

See [Serialization - Version Types](./serialization.md#version-types) for detailed explanation.

## Library Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Examples:
  1.0.0        - Stable release
  1.2.3        - Patch release
  2.0.0-alpha  - Pre-release
  1.0.0-rc.1   - Release candidate
  1.0.0+build  - Build metadata
```

### Version Components

| Component | When to Increment | Example Change |
|-----------|-------------------|----------------|
| **MAJOR** | Breaking API changes | Removing function, changing required signature, changing return type, removing fields |
| **MINOR** | New features (backward compatible) | New function, new optional parameter, new optional field, new event type |
| **PATCH** | Bug fixes (backward compatible) | Fix incorrect calculation, documentation fixes, performance improvements |

### Version Decision Examples

| Change | Version Increment | Reason |
|--------|-------------------|--------|
| Remove `apply_pitch()` function | MAJOR | Breaking - existing code fails |
| Add required parameter to `apply_pitch()` | MAJOR | Breaking - existing calls fail |
| Change `GameState.outs` from int to enum | MAJOR | Breaking - type change |
| Change default value of `GameRules.max_innings` from 9 to None | MAJOR | Breaking - behavior change |
| Add new optional parameter `timeout` to `apply_pitch()` | MINOR | Non-breaking - existing calls work |
| Add new field `GameState.pitch_count` | MINOR | Non-breaking - new functionality |
| Add new event type `balk` | MINOR | Non-breaking - additive |
| Fix RBI calculation bug | PATCH | Non-breaking - bug fix |
| Improve `validate_state()` performance by 50% | PATCH | Non-breaking - optimization |

## Event Schema Versioning

Event payloads have their own schema version, tracked in the event envelope:

```json
{
  "envelope": {
    "event_type": "hit.v1",
    "schema_version": "1",
    ...
  }
}
```

**Important**: `schema_version` is included in `event_id` calculation. Events with different schema versions have different IDs, even if the payload content is logically equivalent.

### Schema Version Changes

| Change Type | Schema Version Impact |
|-------------|----------------------|
| Add optional field to payload | MINOR (new consumers can use, old ignore) |
| Remove field from payload | MAJOR (breaks old consumers) |
| Change field type | MAJOR |
| Rename field | MAJOR |

## Compatibility Policy

### Public API Surface

The following are considered **public API** and subject to SemVer:

| Component | Included in API |
|-----------|-----------------|
| Python functions | `initial_game_state()`, `apply_pitch()`, etc. |
| Python classes | `GameState`, `GameRules`, `Event`, exceptions |
| Python type hints | All exported type annotations |
| JSON schemas | Serialization format |
| Error codes | Exception types and error codes |

### Internal Implementation

The following are **not** part of the public API:

| Component | Notes |
|-----------|-------|
| Internal Rust functions | May change without notice |
| Internal module structure | `_internal` modules |
| Performance characteristics | May change in minor versions |
| Specific error messages | Wording may change |

### Compatibility Matrix

| Change Type | MAJOR | MINOR | PATCH |
|-------------|-------|-------|-------|
| Remove public function | ✓ | | |
| Change function signature | ✓ | | |
| Add required parameter | ✓ | | |
| Change return type | ✓ | | |
| Remove field from data model | ✓ | | |
| Change serialization format (breaking) | ✓ | | |
| Add new public function | | ✓ | |
| Add optional parameter | | ✓ | |
| Add new field to data model | | ✓ | |
| Add new event type | | ✓ | |
| Add new rule option | | ✓ | |
| Fix bug (API unchanged) | | | ✓ |
| Performance improvement | | | ✓ |
| Documentation update | | | ✓ |

## Deprecation Policy

### Deprecation Process

1. **Announcement**: Feature marked as deprecated in MINOR release
2. **Warning Period**: Minimum 2 MINOR versions before removal
3. **Removal**: Feature removed in next MAJOR release

### Marking Deprecations

#### Python

```python
import warnings

def old_function():
    """Deprecated: Use new_function() instead."""
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

#### Rust

```rust
#[deprecated(since = "1.2.0", note = "use new_function instead")]
pub fn old_function() -> Result<()> {
    new_function()
}
```

### Deprecation Timeline Example

```
v1.0.0 - original_api() available
v1.1.0 - original_api() deprecated, new_api() introduced
v1.2.0 - deprecation warning enforced
v2.0.0 - original_api() removed
```

## Release Lifecycle

### Release Types

| Type | Format | Stability | Support |
|------|--------|-----------|---------|
| Stable | `X.Y.Z` | Production ready | Full support |
| Pre-release | `X.Y.Z-alpha.N` | Testing only | Limited support |
| Release Candidate | `X.Y.Z-rc.N` | Near-stable | Bug fixes only |
| LTS | `X.Y.Z` (designated) | Long-term stable | Extended support |

### Support Timeline

```
┌─────────────────────────────────────────────────────────────┐
│  Version 1.x                                                 │
│  ├── Active Development (6 months)                          │
│  ├── Maintenance (6 months)                                 │
│  └── End of Life                                            │
│                                                              │
│  Version 2.x                                                 │
│  ├── Active Development ─────────────────────────►          │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

## Migration Guidelines

### Minor Version Upgrades

Minor version upgrades should be seamless:

```bash
# Before: v1.2.3
pip install baselom-core==1.2.3

# After: v1.3.0
pip install baselom-core==1.3.0
# No code changes required
```

### Major Version Upgrades

Major versions may require code changes. Migration guides are provided:

#### v1.x to v2.x Migration Guide (Example)

```markdown
# Migration Guide: v1.x to v2.x

## Breaking Changes

### 1. GameState Structure Changes

**Before (v1.x):**
```python
state.batting_team  # Returns 'home' or 'away'
```

**After (v2.x):**
```python
state.batting_team  # Returns TeamId enum
str(state.batting_team)  # Use str() for string value
```

### 2. apply_pitch Signature Change

**Before (v1.x):**
```python
state, event = apply_pitch(state, 'ball', rules)
```

**After (v2.x):**
```python
state, event = apply_pitch(state, PitchResult.BALL, rules)
# String form still works but deprecated
```

### 3. Removed Functions

- `legacy_function()` - Use `new_function()` instead
```

### Automated Migration

When possible, migration scripts are provided:

```bash
# Run migration script
python -m baselom_core.migrate v1_to_v2

# Or with codemods
baselom-migrate --from 1.x --to 2.x ./src
```

## Serialization Versioning

### Schema Version

All serialized data includes a `rules_version` field:

```json
{
  "rules_version": "1.2.0",
  "inning": 5,
  ...
}
```

### Forward Compatibility

- New fields added as optional with defaults
- Old data can be read by newer versions

### Backward Compatibility

- Serialization format preserved within MAJOR version
- Migration functions provided for cross-version reading

### Version Check on Deserialization

```python
def deserialize_state(data: dict) -> GameState:
    version = data.get('rules_version', '0.0.0')
    
    if parse_version(version) > CURRENT_VERSION:
        raise SchemaError(
            f"Cannot deserialize future version {version}. "
            f"Current version is {CURRENT_VERSION}."
        )
    
    if parse_version(version).major < CURRENT_VERSION.major:
        # Apply migrations
        data = migrate_state(data, from_version=version)
    
    return _deserialize_state_impl(data)
```

## Version Checking in Code

### Python

```python
from baselom_core import __version__, check_version

# Get version
print(__version__)  # "1.2.3"

# Check minimum version
if check_version("1.2.0"):
    # Use feature from 1.2.0+
    pass
```

### Rust

```rust
use baselom_core::VERSION;

// Version string
println!("Version: {}", VERSION);

// Version tuple
let (major, minor, patch) = baselom_core::version_tuple();
```

## Changelog

All releases are documented in `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- New extra innings tiebreaker option

### Changed
- Improved performance of state validation

### Deprecated
- `old_api()` - use `new_api()` instead

### Removed
- Nothing

### Fixed
- Fixed incorrect RBI calculation with bases loaded

### Security
- Nothing

## [1.2.0] - 2024-02-15

### Added
- Mercy rule support
- Walk-off detection

### Fixed
- Fixed foul tip handling with two strikes

## [1.1.0] - 2024-01-15

### Added
- Extra innings tiebreaker rule
- DH support

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Core game state management
- Basic baseball rules
- Python bindings
```

## Pre-release Versions

### Alpha Releases

```
1.0.0-alpha.1  - First alpha
1.0.0-alpha.2  - Updated alpha
```

- May have incomplete features
- API may change significantly
- Not for production use

### Beta Releases

```
1.0.0-beta.1   - First beta
1.0.0-beta.2   - Updated beta
```

- Feature complete
- API mostly stable
- Testing in non-critical environments

### Release Candidates

```
1.0.0-rc.1     - First release candidate
1.0.0-rc.2     - Updated release candidate
```

- Ready for final testing
- API frozen
- Only critical bug fixes

## Dependency Versioning

### Specifying Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "baselom-core>=1.2.0,<2.0.0",  # Compatible with 1.x
]

# For stricter requirements
dependencies = [
    "baselom-core~=1.2.0",  # 1.2.x only
]
```

### Rust Dependencies

```toml
# Cargo.toml
[dependencies]
serde = "1.0"      # Any 1.x
pyo3 = "0.20"      # Specific minor
```

## See Also

- [Development Guide](./development.md) - Release process
- [Serialization](./serialization.md) - Data format versioning
- [CHANGELOG.md](../CHANGELOG.md) - Release history
