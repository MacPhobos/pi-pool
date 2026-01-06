"""Unit tests for Sensor class.

Tests the Sensor wrapper class that interfaces with sensor devices.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from Sensor import Sensor


@pytest.mark.unit
class TestSensor:
    """Unit tests for Sensor class functionality."""

    @pytest.fixture
    def mock_thermometer(self):
        """Provide mock thermometer device for testing."""
        mock_device = Mock()
        mock_device.getName.return_value = "test_sensor"
        mock_device.getCurrentReading.return_value = 25.5
        mock_device.status.return_value = {
            "test_sensor": 25.5,
            "test_sensor_status": "OK"
        }
        return mock_device

    @pytest.fixture
    def sensor(self, mock_thermometer, mock_db_singleton):
        """Provide Sensor instance with mocked dependencies."""
        return Sensor(mock_thermometer)

    def test_sensor_initialization(self, mock_thermometer, mock_db_singleton):
        """Sensor should initialize with device and set up DB connection."""
        sensor = Sensor(mock_thermometer)

        assert sensor.device == mock_thermometer
        assert sensor.db is not None
        assert sensor.lastDbLogTime > 0

    def test_sensor_get_name(self, sensor, mock_thermometer):
        """Sensor should delegate getName to device."""
        name = sensor.getName()

        assert name == "test_sensor"
        mock_thermometer.getName.assert_called_once()

    def test_sensor_get_current_reading(self, sensor, mock_thermometer):
        """Sensor should delegate getCurrentReading to device."""
        reading = sensor.getCurrentReading()

        assert reading == 25.5
        mock_thermometer.getCurrentReading.assert_called_once()

    def test_sensor_status(self, sensor, mock_thermometer):
        """Sensor should delegate status to device."""
        status = sensor.status()

        assert status["test_sensor"] == 25.5
        assert status["test_sensor_status"] == "OK"
        mock_thermometer.status.assert_called_once()

    def test_sensor_log_to_db_skips_when_recent(self, sensor, mock_db_singleton):
        """Sensor should skip DB logging when last log was recent."""
        # Set lastDbLogTime to current time
        sensor.lastDbLogTime = time.time()

        sensor.logSensorToDb()

        # Should not have called DB
        mock_db_singleton.logSensor.assert_not_called()

    def test_sensor_log_to_db_when_old(self, sensor, mock_db_singleton, mock_thermometer):
        """Sensor should log to DB when last log was over 5 minutes ago."""
        # Set lastDbLogTime to 6 minutes ago
        sensor.lastDbLogTime = time.time() - (6 * 60)

        sensor.logSensorToDb()

        # Should have called DB with sensor name and reading
        mock_db_singleton.logSensor.assert_called_once_with("test_sensor", 25.5)

    def test_sensor_log_to_db_updates_timestamp(self, sensor, mock_db_singleton):
        """Sensor should update lastDbLogTime after logging."""
        # Set lastDbLogTime to 6 minutes ago
        old_time = time.time() - (6 * 60)
        sensor.lastDbLogTime = old_time

        sensor.logSensorToDb()

        # lastDbLogTime should be updated to current time
        assert sensor.lastDbLogTime > old_time
        assert sensor.lastDbLogTime <= time.time()

    def test_sensor_with_different_device(self, mock_db_singleton):
        """Sensor should work with different sensor device types."""
        # Create different mock device
        mock_cpu_temp = Mock()
        mock_cpu_temp.getName.return_value = "cpu_temp"
        mock_cpu_temp.getCurrentReading.return_value = 42.0
        mock_cpu_temp.status.return_value = {"cpu_temp": 42.0}

        sensor = Sensor(mock_cpu_temp)

        assert sensor.getName() == "cpu_temp"
        assert sensor.getCurrentReading() == 42.0
        assert sensor.status()["cpu_temp"] == 42.0
