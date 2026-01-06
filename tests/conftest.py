"""Pytest configuration and shared fixtures for PiPool tests.

This module provides:
- Path configuration to add src/ to Python path
- Environment setup for simulated hardware mode
- Singleton reset fixtures for Config, DB, Event
- Mock fixtures for hardware components
- Test configuration fixtures
"""

import sys
import os
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager

import pytest

# Add src/ to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

# Set hardware mode to simulated BEFORE any imports
os.environ['PIPOOL_HARDWARE_MODE'] = 'simulated'


# ============================================================================
# Singleton Reset Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton instances before each test.

    This ensures test isolation by clearing singleton state.
    Applied automatically to all tests (autouse=True).
    """
    # Import after path is set
    from Config import Config
    from DB import DB
    from Event import Event

    # Reset singleton instances using private attribute pattern
    Config._Config__instance = None
    DB._DB__instance = None
    Event._Event__instance = None

    yield  # Run test

    # Cleanup after test
    Config._Config__instance = None
    DB._DB__instance = None
    Event._Event__instance = None


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config_data():
    """Provide test configuration data as dictionary.

    Returns default configuration suitable for testing with simulated hardware.
    """
    return {
        "tempSensors": {
            "in_to_heater": {
                "name": "temp_sensor_in",
                "device": "/dev/null"  # Simulated path
            },
            "out_from_heater": {
                "name": "temp_sensor_out",
                "device": "/dev/null"
            },
            "temp_ambient": {
                "name": "temp_ambient",
                "device": "/dev/null"
            }
        },
        "pumpPort": 8,
        "heaterPort": 7,
        "lightPort": 6,
        "pumpSpeedS1Port": 1,
        "pumpSpeedS2Port": 2,
        "pumpSpeedS3Port": 3,
        "pumpSpeedS4Port": 4,
        "maxWaterTemp": 33,
        "maxHeaterRuntimeSeconds": 14400,  # Max 4 hours runtime
        "pingTarget": "127.0.0.1",
        "mqttBroker": "127.0.0.1",  # Configurable MQTT broker
        "dbName": "pipool_test",
        "dbUser": "pipool_test",
        "dbPassword": "pipool_test",
        "hardwareMode": "simulated"
    }


@pytest.fixture
def test_config_file(test_config_data, tmp_path):
    """Create temporary config.json file for testing.

    Args:
        test_config_data: Configuration dictionary fixture
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to temporary config file
    """
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(test_config_data, f, indent=2)
    return config_file


@pytest.fixture
def config(test_config_file, monkeypatch):
    """Provide initialized Config singleton for testing.

    Creates Config singleton with test configuration and ensures cleanup.
    Changes working directory to temp dir so Config finds test config.json.

    Args:
        test_config_file: Path to test config file
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Config singleton instance
    """
    from Config import Config

    # Change to temp directory so Config finds our test config.json
    monkeypatch.chdir(test_config_file.parent)

    # Initialize Config singleton
    config_instance = Config()

    yield config_instance

    # Cleanup happens automatically via reset_singletons fixture


# ============================================================================
# Hardware Abstraction Layer (HAL) Fixtures
# ============================================================================

@pytest.fixture
def simulated_gpio():
    """Provide simulated GPIO controller.

    Returns:
        SimulatedGpioController instance for testing GPIO operations
    """
    from hal import HardwareFactory, HardwareMode

    factory = HardwareFactory(HardwareMode.SIMULATED)
    gpio = factory.createGpioController()
    return gpio


@pytest.fixture
def simulated_temp_sensor():
    """Provide simulated temperature sensor.

    Returns:
        SimulatedTemperatureSensor instance with default settings
    """
    from hal import HardwareFactory, HardwareMode

    factory = HardwareFactory(HardwareMode.SIMULATED)
    sensor = factory.createTemperatureSensor("/dev/null", "test_sensor")
    return sensor


@pytest.fixture
def simulated_cpu_monitor():
    """Provide simulated CPU monitor.

    Returns:
        SimulatedCpuMonitor instance for testing CPU temperature
    """
    from hal import HardwareFactory, HardwareMode

    factory = HardwareFactory(HardwareMode.SIMULATED)
    monitor = factory.createCpuMonitor()
    return monitor


@pytest.fixture
def simulated_network_monitor():
    """Provide simulated network monitor.

    Returns:
        SimulatedNetworkMonitor instance for testing network connectivity
    """
    from hal import HardwareFactory, HardwareMode

    factory = HardwareFactory(HardwareMode.SIMULATED)
    monitor = factory.createNetworkMonitor()
    return monitor


@pytest.fixture
def hardware_factory():
    """Provide HardwareFactory in simulated mode.

    Returns:
        HardwareFactory instance configured for SIMULATED mode
    """
    from hal import HardwareFactory, HardwareMode

    return HardwareFactory(HardwareMode.SIMULATED)


# ============================================================================
# Device Component Fixtures
# ============================================================================

@pytest.fixture
def mock_relay_block(simulated_gpio):
    """Provide mock RelayBlock for testing device control.

    Args:
        simulated_gpio: Simulated GPIO controller

    Returns:
        RelayBlock instance using simulated GPIO
    """
    from RelayBlock import RelayBlock

    relay = RelayBlock(simulated_gpio)
    return relay


@pytest.fixture
def mock_sensors(hardware_factory):
    """Provide mock Sensors collection.

    Args:
        hardware_factory: HardwareFactory fixture

    Returns:
        Sensors instance with simulated sensors
    """
    from Sensors import Sensors
    from Config import Config

    # Need Config for sensor names
    config = Config.getInstance()

    sensors = Sensors(hardware_factory)
    return sensors


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Provide mock database for testing without real PostgreSQL.

    Returns:
        Mock DB instance with logDuration, logSensor, logStateChangeEvent, logOpaqueEvent methods
    """
    mock = Mock()
    mock.logDuration = Mock()
    mock.logSensor = Mock()
    mock.logStateChangeEvent = Mock()
    mock.logOpaqueEvent = Mock()
    return mock


@pytest.fixture
def mock_db_singleton(mock_db, monkeypatch):
    """Patch DB.getInstance() to return mock database.

    Args:
        mock_db: Mock DB fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock DB instance
    """
    from DB import DB

    # Patch getInstance to return mock
    monkeypatch.setattr(DB, 'getInstance', lambda: mock_db)

    return mock_db


@pytest.fixture
def mock_event(mock_db):
    """Provide mock Event singleton.

    Args:
        mock_db: Mock DB fixture

    Returns:
        Event instance using mock database
    """
    from Event import Event

    event = Event(mock_db)
    return event


# ============================================================================
# MQTT Fixtures
# ============================================================================

@pytest.fixture
def mock_mqtt_client():
    """Provide mock MQTT client for testing message handling.

    Returns:
        Mock paho.mqtt.client.Client instance
    """
    mock_client = Mock()
    mock_client.connect = Mock()
    mock_client.subscribe = Mock()
    mock_client.publish = Mock()
    mock_client.loop_start = Mock()
    mock_client.loop_stop = Mock()
    mock_client.disconnect = Mock()
    return mock_client


@pytest.fixture
def mock_message_bus(mock_mqtt_client, monkeypatch):
    """Provide MessageBus with mock MQTT client.

    Args:
        mock_mqtt_client: Mock MQTT client fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        MessageBus instance with mocked MQTT client
    """
    import paho.mqtt.client as mqtt
    from MessageBus import MessageBus

    # Patch mqtt.Client to return our mock
    monkeypatch.setattr(mqtt, 'Client', lambda *args, **kwargs: mock_mqtt_client)

    # MessageBus is not a singleton, create new instance
    bus = MessageBus()

    return bus


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def configure_logging(caplog):
    """Configure logging for tests.

    Sets logging level to INFO and captures all logs.
    Applied automatically to all tests.

    Args:
        caplog: Pytest log capture fixture
    """
    caplog.set_level(logging.INFO)
    yield


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
def integration_system(config, mock_relay_block, mock_db, hardware_factory):
    """Provide integrated system components for integration tests.

    Creates a complete system with all major components initialized.

    Args:
        config: Config fixture
        mock_relay_block: RelayBlock fixture
        mock_db: Mock DB fixture
        hardware_factory: HardwareFactory fixture

    Returns:
        Dictionary with all system components
    """
    from Pump import Pump
    from Heater import Heater
    from Light import Light
    from Sensors import Sensors
    from Event import Event
    from Watchdog import Watchdog

    # Create Event with mock DB
    event = Event(mock_db)

    # Create sensors
    sensors = Sensors(hardware_factory)

    # Create devices
    pump = Pump(mock_relay_block)
    heater = Heater(mock_relay_block, pump)
    light = Light(mock_relay_block)

    # Create watchdog
    watchdog = Watchdog(heater, pump)

    return {
        'config': config,
        'relay_block': mock_relay_block,
        'db': mock_db,
        'event': event,
        'sensors': sensors,
        'pump': pump,
        'heater': heater,
        'light': light,
        'watchdog': watchdog,
        'factory': hardware_factory
    }


# ============================================================================
# Utility Context Managers
# ============================================================================

@contextmanager
def does_not_raise():
    """Context manager for tests expecting no exception.

    Usage:
        with does_not_raise():
            some_operation()
    """
    yield


# ============================================================================
# Parametrize Helpers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interactions")
    config.addinivalue_line("markers", "safety: Safety-critical tests (heater interlocks, watchdog)")
    config.addinivalue_line("markers", "slow: Tests that take more than 1 second")
    config.addinivalue_line("markers", "e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "hardware: Tests requiring real hardware (skip in CI)")
