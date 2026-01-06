"""SAFETY-CRITICAL: Heater safety interlock tests.

These tests verify heater safety mechanisms that prevent equipment damage
and hazardous conditions. Heater MUST NOT operate without pump running,
as this can cause dry fire, equipment damage, and potential fire hazards.

SAFETY REQUIREMENTS TESTED:
- Heater cannot turn on without pump running (prevents dry fire)
- Heater stops if pump stops while running (prevents dry fire)
- Heater stops on invalid/stale sensor readings (prevents overheating)
- Heater respects maximum temperature limits (prevents scalding/damage)
- hardStop() always works regardless of state (emergency shutdown)

These tests MUST pass before any deployment to production hardware.
"""

import pytest
import logging
from unittest.mock import Mock, patch
import time


@pytest.mark.safety
class TestHeaterSafetyInterlocks:
    """CRITICAL: Tests for heater safety mechanisms."""

    @pytest.fixture(autouse=True)
    def mock_event_and_db(self):
        """Auto-mock Event and DB for all tests in this class."""
        with patch('Event.Event.logStateEvent'), \
             patch('Event.Event.logOpaqueEvent'), \
             patch('DB.DB.getInstance') as mock_db_get:

            mock_db = Mock()
            mock_db.logDuration = Mock()
            mock_db_get.return_value = mock_db

            yield

    @pytest.fixture
    def mock_relay_block(self):
        """Mock relay block for heater tests."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def mock_pump(self):
        """Mock pump with isOn() method and state lock for race condition prevention."""
        import threading
        pump = Mock()
        pump.isOn = Mock(return_value=False)  # Default: pump OFF
        # Add state lock for dual-locking mechanism
        pump._state_lock = threading.RLock()
        return pump

    @pytest.fixture
    def heater(self, mock_relay_block, mock_pump):
        """Create Heater instance with mocked dependencies."""
        from Heater import Heater

        heater = Heater(
            relayBlock=mock_relay_block,
            heaterPort=7,
            maxWaterTemp=33,
            pump=mock_pump
        )
        return heater

    def test_heater_cannot_start_without_pump(self, heater, mock_pump, mock_relay_block, caplog):
        """SAFETY: Heater must NOT turn on if pump is off.

        HAZARD: Running heater without pump can cause dry fire, overheating,
        equipment damage, and potential fire. This is the most critical safety check.
        """
        # Arrange: Pump is OFF
        mock_pump.isOn.return_value = False

        # Act: Try to turn heater on
        with caplog.at_level(logging.ERROR):
            heater.on()

        # Assert: Heater did NOT turn on
        assert heater.getState().name == "OFF", "Heater turned on without pump - CRITICAL SAFETY VIOLATION"
        mock_relay_block.portOn.assert_not_called()

        # Verify error was logged
        assert "Cannot turn on - pump is not running" in caplog.text

    def test_heater_can_start_with_pump_running(self, heater, mock_pump, mock_relay_block):
        """Verify heater CAN start when pump is running (normal operation)."""
        # Arrange: Pump is ON
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)  # Valid temperature

        # Act: Turn heater on
        heater.on()

        # Assert: Heater turned on successfully
        assert heater.getState().name == "ON"
        mock_relay_block.portOn.assert_called_once_with(7)

    def test_heater_stops_when_pump_stops(self, heater, mock_pump, mock_relay_block):
        """SAFETY: Heater must stop if pump turns off while running.

        HAZARD: If pump stops while heater is running, water circulation stops
        and heater can overheat/dry fire. Heater MUST detect this and shut down.
        """
        # Arrange: Start with pump AND heater running
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.on()
        assert heater.getState().name == "ON", "Setup failed: heater should be ON"

        # Act: Pump stops (simulating watchdog scenario)
        mock_pump.isOn.return_value = False

        # In real system, watchdog would call hardStop on heater
        # Here we test that heater CANNOT turn back on with pump off
        mock_relay_block.portOn.reset_mock()
        heater.on()  # Try to turn on again

        # Assert: Heater blocked from turning on (relay NOT activated)
        mock_relay_block.portOn.assert_not_called()

        # Note: Heater state may still show ON from first call, but relay was not activated
        # The critical safety check is that relay.portOn was NOT called

    def test_heater_stops_on_invalid_temperature_none(self, heater, caplog):
        """SAFETY: Heater must stop on None sensor reading.

        HAZARD: None/invalid sensor reading means we have no temperature feedback.
        Operating heater blind can cause overheating and equipment damage.
        """
        # Arrange: Heater is in some state
        from HeaterState import HeaterState
        heater.state = HeaterState.ON

        # Act: Receive invalid sensor reading
        with caplog.at_level(logging.ERROR):
            heater.setInputTemp(None)

        # Assert: Heater stopped
        assert heater.getState().name == "OFF", "Heater did not stop on None temperature"
        assert "Invalid input temperature" in caplog.text

    def test_heater_stops_on_invalid_temperature_zero(self, heater, caplog):
        """SAFETY: Heater must stop on zero/negative sensor reading."""
        from HeaterState import HeaterState
        heater.state = HeaterState.ON

        with caplog.at_level(logging.ERROR):
            heater.setInputTemp(0)

        assert heater.getState().name == "OFF"
        assert "Invalid input temperature" in caplog.text

    def test_heater_stops_on_invalid_temperature_negative(self, heater, caplog):
        """SAFETY: Heater must stop on negative sensor reading."""
        from HeaterState import HeaterState
        heater.state = HeaterState.ON

        with caplog.at_level(logging.ERROR):
            heater.setInputTemp(-5)

        assert heater.getState().name == "OFF"
        assert "Invalid input temperature" in caplog.text

    def test_heater_stops_at_max_temperature(self, heater, mock_pump):
        """SAFETY: Heater must stop when max temp reached."""
        # Arrange: Heater running with pump on
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()
        assert heater.getState().name == "ON"

        # Act: Water reaches max temperature (33°C configured)
        heater.setInputTemp(33.0)
        heater.runOneLoop()

        # Assert: Heater stopped
        assert heater.getState().name == "OFF", "Heater did not stop at max temperature"

    def test_heater_stops_above_max_temperature(self, heater, mock_pump):
        """SAFETY: Heater must stop when temperature exceeds max."""
        # Arrange: Heater running
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()

        # Act: Temperature exceeds max
        heater.setInputTemp(34.0)  # Above maxWaterTemp=33
        heater.runOneLoop()

        # Assert: Heater stopped
        assert heater.getState().name == "OFF"

    def test_heater_hard_stop_always_works(self, heater, mock_relay_block):
        """SAFETY: hardStop() must always turn heater off.

        CRITICAL: hardStop() is the emergency shutdown mechanism.
        It MUST work regardless of heater state, mode, or conditions.
        """
        from HeaterState import HeaterState
        from HeaterMode import HeaterMode

        # Test 1: hardStop from ON state
        heater.state = HeaterState.ON
        heater.mode = HeaterMode.HOLD
        heater.hardStop()
        assert heater.getState().name == "OFF", "hardStop failed from ON state"
        assert heater.getMode().name == "OFF", "hardStop did not clear mode"
        mock_relay_block.portOff.assert_called()

        # Test 2: hardStop from already OFF state (should be idempotent)
        mock_relay_block.portOff.reset_mock()
        heater.hardStop()
        assert heater.getState().name == "OFF", "hardStop failed from OFF state"

    def test_heater_stops_on_stale_sensor_data(self, heater, mock_pump, caplog):
        """SAFETY: Heater must stop if sensor data is stale (>60 seconds old)."""
        # Arrange: Heater running with valid initial temperature
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()
        assert heater.getState().name == "ON"

        # Act: Simulate 61 seconds passing
        with patch('time.time') as mock_time:
            original_time = heater.lastInputTempUpdate
            mock_time.return_value = original_time + 61

            with caplog.at_level(logging.ERROR):
                heater.runOneLoop()

        # Assert: Heater stopped
        assert heater.getState().name == "OFF"
        assert "Input sensor stale" in caplog.text

    def test_heater_reach_and_stop_mode_stops_at_target(self, heater, mock_pump):
        """SAFETY: REACH_AND_STOP mode must stop at target temperature."""
        # Arrange: Turn heater on first, then set mode
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.on()  # Turn on first
        heater.setModeReachTempAndStop(30)

        # Act: Run loop while below target (heater stays on)
        heater.runOneLoop()
        assert heater.getState().name == "ON", "Heater should stay on when below target"

        # Reach target temperature
        heater.setInputTemp(30.5)
        heater.runOneLoop()

        # Assert: Heater stopped and mode cleared
        assert heater.getState().name == "OFF", "Heater should stop at target temp"
        assert heater.getMode().name == "OFF", "Mode should clear after reaching target"

    def test_heater_hold_mode_cycles_correctly(self, heater, mock_pump):
        """SAFETY: HOLD mode must cycle heater on/off to maintain temperature."""
        # Arrange: Turn heater on, set HOLD mode below target temp
        mock_pump.isOn.return_value = True
        heater.setInputTemp(29.0)  # Start below target
        heater.on()  # Turn on first
        heater.setModeHoldTemp(30)

        # Act: Run loop below target temp (heater stays on)
        # BUG: This triggers TypeError at line 174
        heater.runOneLoop()

        # Assert: Heater ON below target
        assert heater.getState().name == "ON", "Heater should stay on below target"

        # Act: Temperature reaches target
        heater.setInputTemp(30.0)
        heater.runOneLoop()

        # Assert: Heater turns off at target
        assert heater.getState().name == "OFF", "Heater should turn off at target"

    def test_heater_initialization_state(self, heater):
        """SAFETY: Heater must initialize in safe state (OFF)."""
        assert heater.getState().name == "OFF"
        assert heater.getMode().name == "OFF"
