# Testing Framework - DeepDiver

## ✅ Setup Complete

A comprehensive pytest testing framework has been established for the DeepDiver trading system.

## Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_supabase.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Fixtures and configuration
├── test_supabase.py      # Supabase database tests (12 tests)
├── test_utils.py         # Utility function tests (10 tests)
└── README.md             # Detailed testing guide
```

## Test Coverage

### ✅ Supabase Operations (12 tests)
- **Read Operations** (3 tests)
  - Settings table
  - Journal with filters
  - Alerts table

- **Write Operations** (2 tests)
  - Insert journal entry
  - Insert alert

- **Update Operations** (2 tests)
  - Update journal entry
  - Upsert setting

- **Delete Operations** (2 tests)
  - Delete journal entry
  - Delete alert

- **Complex Queries** (3 tests)
  - Order by
  - Multiple filters
  - Limit and offset (pagination)

### ✅ Utility Functions (10 tests)
- **Settings Helpers** (2 tests)
  - Get settings
  - Update setting

- **Alert Helpers** (3 tests)
  - Get all alerts
  - Add alert
  - Delete alert

- **Position Helpers** (3 tests)
  - Get all positions
  - Add position
  - Filter positions by status

- **Scan Helpers** (2 tests)
  - Get latest scan
  - Get all scans

## Test Results

```
======================= 22 passed, 3 warnings in 14.81s ========================
```

**Status**: ✅ All tests passing
**Coverage**: Core Supabase read/write operations
**Runtime**: ~15 seconds

## Key Features

1. **Automatic Cleanup**: Fixtures auto-create and cleanup test data
2. **Test Isolation**: Each test runs independently
3. **Lazy Imports**: Fixed circular dependency issues
4. **Markers**: Tests organized by type (unit, integration, supabase)
5. **Comprehensive**: Covers CRUD operations on all major tables

## Configuration

### pytest.ini
- Test discovery patterns
- Output formatting
- Test markers
- Environment variables

### conftest.py Fixtures
- `app` - Flask application instance
- `supabase_client` - Database client
- `test_journal_entry` - Auto-managed journal entry
- `test_alert` - Auto-managed alert
- `clean_test_data` - Data cleanup

## Technical Improvements Made

1. **Lazy Supabase Import**: Added `_get_supabase()` helper to avoid circular dependencies
2. **Test Fixtures**: Automatic setup/teardown for test data
3. **Proper Markers**: Organized tests by type (integration, supabase)
4. **Dev Dependencies**: Added pytest, pytest-cov, pytest-mock, pytest-env

## Next Steps

Consider adding tests for:
- [ ] Agent tools (`app/agents/tools.py`)
- [ ] Wilson agent behavior
- [ ] API endpoints (`app/dashboard/routes.py`)
- [ ] Market data fetching (Alpaca integration)
- [ ] Scheduled tasks (`app/tasks.py`)
- [ ] Error handling scenarios
- [ ] Integration tests with real market data

## Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-env>=1.3.2",
    "pytest-mock>=3.12.0",
]
```

Install with: `uv sync --extra dev`

## Documentation

See `tests/README.md` for detailed testing guide including:
- Running tests
- Test markers
- Writing new tests
- Best practices
- Troubleshooting
