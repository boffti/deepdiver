# DeepDiver Test Suite

## Overview

This directory contains the pytest-based test suite for the DeepDiver trading system.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_supabase.py      # Supabase database operation tests
├── test_utils.py         # Utility function tests
└── README.md             # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_supabase.py
```

### Run specific test class
```bash
pytest tests/test_supabase.py::TestSupabaseReadOperations
```

### Run specific test
```bash
pytest tests/test_supabase.py::TestSupabaseReadOperations::test_read_settings
```

### Run tests by marker
```bash
# Run only Supabase tests
pytest -m supabase

# Run only integration tests
pytest -m integration

# Run only unit tests (fast, no external dependencies)
pytest -m unit

# Exclude slow tests
pytest -m "not slow"
```

### Run with coverage report
```bash
pytest --cov=app --cov-report=html
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests requiring external services
- `@pytest.mark.supabase` - Tests requiring Supabase connection
- `@pytest.mark.slow` - Slow-running tests

## Prerequisites

### Environment Variables

Tests require the following environment variables in `.env`:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
OPENROUTER_API_KEY=your_openrouter_key
```

### Database Setup

Ensure the Supabase database schema is created:

1. Go to Supabase SQL Editor
2. Run `docs/supabase-schema.sql`

## Fixtures

Common fixtures are defined in `conftest.py`:

- `app` - Flask application instance
- `supabase_client` - Supabase client for testing
- `test_journal_entry` - Auto-created and cleaned up journal entry
- `test_alert` - Auto-created and cleaned up alert
- `clean_test_data` - Ensures test data is cleaned before/after tests

## Writing New Tests

### Example Test

```python
import pytest

@pytest.mark.supabase
@pytest.mark.integration
def test_example(supabase_client, test_journal_entry):
    """Test description"""
    # Arrange
    entry_id = test_journal_entry['id']

    # Act
    result = supabase_client.table('journal') \
        .select('*') \
        .eq('id', entry_id) \
        .execute()

    # Assert
    assert result.data is not None
    assert result.data[0]['id'] == entry_id
```

### Best Practices

1. **Use fixtures** for setup/teardown
2. **Mark tests** appropriately (unit, integration, etc.)
3. **Clean up** test data (fixtures handle this automatically)
4. **Use descriptive names** for test functions
5. **Follow AAA pattern** (Arrange, Act, Assert)
6. **Test one thing** per test function
7. **Use parametrize** for testing multiple inputs

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
```

## Troubleshooting

### Tests are skipped

If you see "Supabase not configured", check:
- `.env` file exists
- `SUPABASE_URL` and `SUPABASE_KEY` are set
- Supabase service is running

### Database errors

If tests fail with database errors:
- Verify schema is created (`docs/supabase-schema.sql`)
- Check Supabase connection and credentials
- Ensure tables exist in Supabase dashboard

### Cleanup issues

If test data persists:
- Check fixture cleanup logic in `conftest.py`
- Manually clean test data: `DELETE FROM journal WHERE agent_name = 'TestAgent'`
