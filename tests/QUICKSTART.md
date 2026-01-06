# Pytest Quick Reference

## Installation

```bash
# Install test dependencies
uv pip install -e ".[test]"
```

## Common Commands

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/unit/test_config.py
```

### Run specific test
```bash
pytest tests/unit/test_config.py::test_config_loads_from_file
```

### Run by marker
```bash
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m safety         # Safety-critical tests only
pytest -m "not slow"     # Exclude slow tests
```

### Run with coverage (if sqlite3 available)
```bash
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing
```

### Run in parallel (faster)
```bash
pytest -n auto           # Auto-detect CPUs
pytest -n 4              # 4 workers
```

### Debugging
```bash
pytest -s                # Show print statements
pytest --pdb             # Drop into debugger on failure
pytest -vv               # Extra verbose
pytest --showlocals      # Show local variables in failures
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, isolated)
├── integration/          # Integration tests (component interactions)
├── safety/              # Safety-critical tests (must pass 100%)
└── e2e/                 # End-to-end workflow tests
```

## Writing a Test

```python
import pytest
from Pump import Pump
from PumpState import PumpState

@pytest.mark.unit
def test_pump_turns_on(mock_relay_block):
    """Test pump can be turned on."""
    pump = Pump(mock_relay_block)

    pump.on()

    assert pump.state == PumpState.ON
    mock_relay_block.setPortOn.assert_called()
```

## Available Fixtures

- `config` - Initialized Config singleton
- `simulated_gpio` - Simulated GPIO controller
- `mock_relay_block` - RelayBlock with simulated GPIO
- `mock_db` - Mock database (no PostgreSQL needed)
- `mock_mqtt_client` - Mock MQTT client
- `integration_system` - Complete system with all components

See `tests/conftest.py` for full list of fixtures.

## Tips

1. Tests run in **simulated mode** automatically (no hardware needed)
2. Singletons are **reset before each test** (test isolation)
3. Use **descriptive test names** that explain what's being tested
4. Tag tests with **markers** (@pytest.mark.unit, etc.)
5. Mock external dependencies (MQTT, database, hardware)

## Troubleshooting

### Coverage not working (sqlite3 error)
Coverage requires Python with sqlite3 compiled in. If not available, run without coverage:
```bash
pytest  # Coverage disabled by default in pytest.ini
```

### Import errors
The conftest.py adds `src/` to Python path automatically.

### Singleton errors
The `reset_singletons` fixture resets Config, DB, Event before each test.
