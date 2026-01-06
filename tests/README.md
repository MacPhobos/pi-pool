# PiPool Test Suite

Comprehensive testing infrastructure for the PiPool Raspberry Pi pool automation system.

## Directory Structure

```
tests/
├── conftest.py           # Shared fixtures and pytest configuration
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for component interactions
├── safety/              # Safety-critical tests (heater interlocks, watchdog)
└── e2e/                 # End-to-end workflow tests
```

## Installation

Install test dependencies using `uv`:

```bash
# Install test dependencies
uv pip install -e ".[test]"

# OR using requirements-test.txt
uv pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Safety-critical tests only
pytest -m safety

# E2E tests only
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"
```

### Run specific test files
```bash
# Single file
pytest tests/unit/test_config.py

# Multiple files
pytest tests/unit/test_config.py tests/unit/test_pump.py
```

### Run with coverage
```bash
# HTML coverage report (opens htmlcov/index.html)
pytest --cov=src --cov-report=html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# Coverage with minimum threshold
pytest --cov=src --cov-fail-under=90
```

### Run in parallel (faster)
```bash
# Auto-detect number of CPUs
pytest -n auto

# Specific number of workers
pytest -n 4
```

### Verbose output
```bash
# Show all test names and results
pytest -v

# Show captured output (print statements)
pytest -s

# Show local variables in failures
pytest --showlocals
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.safety` - Safety-critical tests (heater/pump interlocks)
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.hardware` - Tests requiring real hardware (skip in CI)

Example usage:
```python
import pytest

@pytest.mark.unit
def test_pump_on_off(mock_relay_block):
    """Test pump on/off state transitions."""
    from Pump import Pump
    pump = Pump(mock_relay_block)
    # ... test code ...
```

## Available Fixtures

### Configuration Fixtures
- `test_config_data` - Test configuration dictionary
- `test_config_file` - Temporary config.json file
- `config` - Initialized Config singleton

### Hardware Fixtures (Simulated)
- `simulated_gpio` - Simulated GPIO controller
- `simulated_temp_sensor` - Simulated temperature sensor
- `simulated_cpu_monitor` - Simulated CPU monitor
- `simulated_network_monitor` - Simulated network monitor
- `hardware_factory` - HardwareFactory in simulated mode

### Device Fixtures
- `mock_relay_block` - RelayBlock with simulated GPIO
- `mock_sensors` - Sensors collection with simulated sensors

### Database Fixtures
- `mock_db` - Mock database (no PostgreSQL required)
- `mock_db_singleton` - Patched DB.getInstance() returning mock
- `mock_event` - Event singleton with mock database

### MQTT Fixtures
- `mock_mqtt_client` - Mock MQTT client
- `mock_message_bus` - MessageBus with mock MQTT

### Integration Fixtures
- `integration_system` - Complete system with all components

### Auto-applied Fixtures
- `reset_singletons` - Resets Config, DB, Event before each test (auto)
- `configure_logging` - Sets up logging for tests (auto)

## Writing Tests

### Unit Test Example
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

### Integration Test Example
```python
import pytest

@pytest.mark.integration
def test_heater_requires_pump(integration_system):
    """Test heater cannot turn on without pump running."""
    heater = integration_system['heater']
    pump = integration_system['pump']

    # Pump off
    pump.off()

    # Try to turn heater on
    heater.on()

    # Heater should remain off (safety interlock)
    assert heater.state == HeaterState.OFF
```

### Safety Test Example
```python
import pytest

@pytest.mark.safety
def test_watchdog_stops_heater_when_pump_off(integration_system):
    """Test watchdog safety: heater stops if pump turns off."""
    watchdog = integration_system['watchdog']
    heater = integration_system['heater']
    pump = integration_system['pump']

    # Start with pump on and heater on
    pump.on()
    heater.on()

    # Simulate pump failure
    pump.off()

    # Run watchdog check
    watchdog.check()

    # Heater should be stopped by watchdog
    assert heater.state == HeaterState.OFF
```

## Test Isolation

All tests are isolated via:

1. **Singleton Reset**: `reset_singletons` fixture automatically resets Config, DB, Event before each test
2. **Simulated Hardware**: `PIPOOL_HARDWARE_MODE=simulated` environment variable set automatically
3. **Temporary Files**: `tmp_path` fixture provides clean temp directories
4. **Mock Database**: Tests use mock DB by default (no PostgreSQL required)

## Continuous Integration

For CI/CD pipelines:

```bash
# Run all tests except hardware-dependent ones
pytest -m "not hardware"

# Run with coverage and fail if < 80%
pytest --cov=src --cov-fail-under=80 --cov-report=xml

# Generate JUnit XML for CI
pytest --junit-xml=junit.xml
```

## Debugging Tests

### Run single test with verbose output
```bash
pytest tests/unit/test_pump.py::test_pump_on_off -vv -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Show print statements
```bash
pytest -s
```

### Show local variables in tracebacks
```bash
pytest --showlocals
```

## Best Practices

1. **Use markers** - Tag tests with appropriate markers (@pytest.mark.unit, etc.)
2. **Test isolation** - Each test should be independent and not rely on global state
3. **Descriptive names** - Use clear test names that describe what is being tested
4. **Arrange-Act-Assert** - Structure tests clearly with setup, action, and assertion
5. **Mock external dependencies** - Use fixtures to mock MQTT, database, hardware
6. **Test edge cases** - Include tests for error conditions and boundary cases
7. **Safety first** - Tag safety-critical tests with @pytest.mark.safety

## Coverage Goals

- **Overall**: 90%+ coverage
- **Safety-critical**: 100% coverage (Heater, Pump, Watchdog)
- **Core logic**: 95%+ coverage (Config, DB, Event, Sensors)
- **Integration**: 85%+ coverage (MessageBus, device coordination)

## Troubleshooting

### Import errors
Ensure `src/` is in Python path. The conftest.py handles this automatically.

### Singleton already initialized
The `reset_singletons` fixture should handle this. If issues persist, check that tests don't manually initialize singletons before fixtures run.

### Hardware mode not simulated
Verify `PIPOOL_HARDWARE_MODE=simulated` is set. The conftest.py sets this automatically.

### Database connection errors
Tests should use `mock_db` fixture by default. If tests require real database, use appropriate fixture and mark as `@pytest.mark.integration`.
