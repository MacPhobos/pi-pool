"""Tests for thermometer error handling.

This module tests that the thermometer returns None instead of stale data
when a sensor read fails.

SAFETY REQUIREMENT:
Stale temperature data is dangerous. If a sensor fails:
- Operating on old data could cause overheating (heater thinks water is cold)
- Callers must be able to detect failures and respond (e.g., safety shutdown)
- Returning the last known value masks the failure

The fix returns None on error, requiring callers to handle the failure case.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestThermometerErrorHandling:
    """Tests for thermometer returning None on sensor read error."""

    @pytest.fixture
    def mock_sensor(self):
        """Create mock temperature sensor."""
        sensor = Mock()
        sensor.readTemperature = Mock(return_value=("test_sensor", 25.0))
        return sensor

    @pytest.fixture
    def thermometer(self, mock_sensor):
        """Create Thermometer with mock sensor."""
        from Thermometer import Thermometer

        config = {
            "name": "test_sensor",
            "device": "/dev/null"
        }

        # Inject mock sensor
        therm = Thermometer(config, temperatureSensor=mock_sensor)
        return therm

    def test_thermometer_returns_none_on_read_error(self, thermometer, mock_sensor, caplog):
        """Thermometer must return None on sensor read error."""
        # Simulate sensor read failure
        mock_sensor.readTemperature = Mock(side_effect=Exception("Sensor disconnected"))

        with caplog.at_level(logging.ERROR):
            name, temp = thermometer.readTemp()

        # Verify None returned instead of stale data
        assert temp is None, "Temperature should be None on sensor error"
        assert name == "test_sensor", "Sensor name should still be returned"
        assert "read error" in caplog.text
        assert "Sensor disconnected" in caplog.text

    def test_thermometer_returns_value_on_success(self, thermometer, mock_sensor):
        """Verify normal operation returns valid temperature."""
        mock_sensor.readTemperature = Mock(return_value=("test_sensor", 28.5))

        name, temp = thermometer.readTemp()

        assert temp == 28.5, "Temperature should be returned on success"
        assert name == "test_sensor"

    def test_thermometer_does_not_return_stale_data(self, thermometer, mock_sensor):
        """After error, must not return previous reading."""
        # First: successful read
        mock_sensor.readTemperature = Mock(return_value=("test_sensor", 30.0))
        name1, temp1 = thermometer.readTemp()
        assert temp1 == 30.0, "First read should succeed"

        # Second: failure - should NOT return 30.0
        mock_sensor.readTemperature = Mock(side_effect=IOError("I/O error"))
        name2, temp2 = thermometer.readTemp()

        assert temp2 is None, "Error read must return None, not stale 30.0"
        assert temp2 != 30.0, "Must not return previous reading"

    def test_thermometer_current_temp_not_updated_on_error(self, thermometer, mock_sensor):
        """Verify currentTemp is not updated when sensor fails."""
        # First: successful read
        mock_sensor.readTemperature = Mock(return_value=("test_sensor", 25.0))
        thermometer.readTemp()
        assert thermometer.getCurrentTemp() == 25.0

        # Second: failure
        mock_sensor.readTemperature = Mock(side_effect=Exception("Error"))
        thermometer.readTemp()

        # currentTemp should still be the last GOOD reading
        # (but readTemp() returns None for new reads)
        assert thermometer.getCurrentTemp() == 25.0, "currentTemp preserves last good reading"

    def test_thermometer_handles_various_exceptions(self, thermometer, mock_sensor):
        """Verify various exception types are handled correctly."""
        exception_types = [
            IOError("Device not found"),
            OSError("Permission denied"),
            ValueError("Invalid reading"),
            TimeoutError("Read timeout"),
            Exception("Generic error")
        ]

        for exc in exception_types:
            mock_sensor.readTemperature = Mock(side_effect=exc)

            name, temp = thermometer.readTemp()

            assert temp is None, f"Should return None for {type(exc).__name__}"

    def test_thermometer_status_with_error(self, thermometer, mock_sensor):
        """Verify status() handles None temperature."""
        mock_sensor.readTemperature = Mock(side_effect=Exception("Error"))

        status = thermometer.status()

        assert "test_sensor" in status
        assert status["test_sensor"] is None, "Status should show None for failed sensor"


@pytest.mark.safety
class TestThermometerSafetyIntegration:
    """Integration tests for thermometer with heater safety."""

    @pytest.fixture(autouse=True)
    def mock_event_and_db(self):
        """Auto-mock Event and DB."""
        with patch('Event.Event.logStateEvent'), \
             patch('Event.Event.logOpaqueEvent'), \
             patch('DB.DB.getInstance') as mock_db_get:
            mock_db = Mock()
            mock_db.logDuration = Mock()
            mock_db_get.return_value = mock_db
            yield

    def test_heater_handles_none_temperature(self):
        """Verify Heater properly handles None temperature input."""
        import threading
        from Heater import Heater
        from HeaterState import HeaterState

        mock_relay = Mock()
        mock_relay.portOn = Mock()
        mock_relay.portOff = Mock()

        mock_pump = Mock()
        mock_pump.isOn = Mock(return_value=True)
        mock_pump._state_lock = threading.RLock()

        heater = Heater(
            relayBlock=mock_relay,
            heaterPort=7,
            maxWaterTemp=33,
            pump=mock_pump,
            maxRuntimeSeconds=14400
        )

        # Turn heater on first
        heater.setInputTemp(25.0)
        heater.on()
        assert heater.isOn() is True

        # Now set None temperature (simulating sensor failure)
        # Heater.setInputTemp should handle this as invalid
        heater.setInputTemp(None)

        # Heater should have stopped due to invalid temperature
        assert heater.getState() == HeaterState.OFF, "Heater should stop on None temperature"
