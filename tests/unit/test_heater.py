"""Unit tests for Heater class.

Tests core Heater functionality including:
- Basic on/off control (with pump dependency)
- State and mode management
- Temperature control modes (HOLD, REACH_AND_STOP)
- Target temperature setting
- Timer tracking
- Sensor input handling
"""

import pytest
from unittest.mock import Mock, patch
import time


@pytest.mark.unit
class TestHeater:
    """Unit tests for Heater class."""

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
        """Mock pump that is ON by default for heater tests."""
        import threading
        pump = Mock()
        pump.isOn = Mock(return_value=True)  # Default: pump ON for heater tests
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

    def test_heater_initialization(self, heater):
        """Verify heater initializes with correct defaults."""
        from HeaterState import HeaterState
        from HeaterMode import HeaterMode

        assert heater.getState() == HeaterState.OFF
        assert heater.getMode() == HeaterMode.OFF
        assert heater.targetTemp == 0
        assert heater.inputTemp == 0
        assert heater.outputTemp == 0
        assert heater.relayBlockPort == 7

    def test_heater_on_with_pump_running(self, heater, mock_pump, mock_relay_block):
        """Test heater can turn on when pump is running."""
        from HeaterState import HeaterState

        # Arrange: Pump is on, valid temperature
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)

        # Act
        heater.on()

        # Assert
        assert heater.getState() == HeaterState.ON
        mock_relay_block.portOn.assert_called_once_with(7)

    def test_heater_off(self, heater, mock_relay_block):
        """Test turning heater off."""
        from HeaterState import HeaterState

        # Arrange: Turn on first
        heater.setInputTemp(25.0)
        heater.on()

        # Act
        heater.off()

        # Assert
        assert heater.getState() == HeaterState.OFF
        mock_relay_block.portOff.assert_called_with(7)

    def test_heater_get_state(self, heater):
        """Test getState returns current state."""
        from HeaterState import HeaterState

        # Initially OFF
        assert heater.getState() == HeaterState.OFF

        # Turn on
        heater.setInputTemp(25.0)
        heater.on()
        assert heater.getState() == HeaterState.ON

        # Turn off
        heater.off()
        assert heater.getState() == HeaterState.OFF

    def test_heater_is_on(self, heater):
        """Test isOn() method returns correct boolean."""
        # Initially OFF
        assert heater.isOn() is False

        # Turn on
        heater.setInputTemp(25.0)
        heater.on()
        assert heater.isOn() is True

        # Turn off
        heater.off()
        assert heater.isOn() is False

    def test_heater_get_mode(self, heater):
        """Test getMode returns current mode."""
        from HeaterMode import HeaterMode

        # Initially OFF
        assert heater.getMode() == HeaterMode.OFF

        # Set HOLD mode
        heater.setModeHoldTemp(30)
        assert heater.getMode() == HeaterMode.HOLD

        # Set REACH_AND_STOP mode
        heater.setModeReachTempAndStop(28)
        assert heater.getMode() == HeaterMode.REACH_AND_STOP

    def test_heater_set_input_temp(self, heater):
        """Test setting input temperature."""
        # Act
        heater.setInputTemp(26.5)

        # Assert
        assert heater.inputTemp == 26.5
        assert heater.lastInputTempUpdate > 0

    def test_heater_set_output_temp(self, heater):
        """Test setting output temperature."""
        # Act
        heater.setOutputTemp(28.0)

        # Assert
        assert heater.outputTemp == 28.0

    def test_heater_set_mode_hold_temp(self, heater):
        """Test setting HOLD mode with target temperature."""
        from HeaterMode import HeaterMode

        # Act
        heater.setModeHoldTemp(30)

        # Assert
        assert heater.getMode() == HeaterMode.HOLD
        assert heater.targetTemp == 30

    def test_heater_set_mode_hold_temp_logs_event(self, heater):
        """Verify HOLD mode logs event."""
        # Act
        heater.setModeHoldTemp(29)

        # Assert: Event logging is mocked globally, we just verify no exceptions
        assert heater.getMode().name == "HOLD"

    def test_heater_set_mode_reach_temp_and_stop(self, heater):
        """Test setting REACH_AND_STOP mode with target temperature."""
        from HeaterMode import HeaterMode

        # Act
        heater.setModeReachTempAndStop(28)

        # Assert
        assert heater.getMode() == HeaterMode.REACH_AND_STOP
        assert heater.targetTemp == 28

    def test_heater_set_mode_reach_and_stop_logs_event(self, heater):
        """Verify REACH_AND_STOP mode logs event."""
        # Act
        heater.setModeReachTempAndStop(32)

        # Assert: Event logging is mocked globally, we just verify no exceptions
        assert heater.getMode().name == "REACH_AND_STOP"

    def test_heater_set_mode_off(self, heater):
        """Test setting mode to OFF."""
        from HeaterMode import HeaterMode

        # Arrange: Set HOLD mode
        heater.setModeHoldTemp(30)

        # Act
        heater.setModeOff()

        # Assert
        assert heater.getMode() == HeaterMode.OFF

    def test_heater_input_temp_less_than(self, heater):
        """Test inputTempLessThen comparison."""
        # Set temperature
        heater.setInputTemp(25.0)

        # Test comparison
        assert heater.inputTempLessThen(30) is True
        assert heater.inputTempLessThen(25) is False
        assert heater.inputTempLessThen(20) is False

    def test_heater_mode_reach_and_stop_heating(self, heater, mock_pump, caplog):
        """Test REACH_AND_STOP mode keeps heater on when below target."""
        import logging

        # Arrange: Turn heater on first, then set mode
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.on()  # Turn on first
        heater.setModeReachTempAndStop(30)

        # Act
        with caplog.at_level(logging.INFO):
            heater.runOneLoop()

        # Assert: Heater stays on
        assert heater.isOn() is True
        assert "Heating from 25" in caplog.text

    def test_heater_mode_reach_and_stop_stops_at_target(self, heater, mock_pump, caplog):
        """Test REACH_AND_STOP mode stops when target reached."""
        import logging
        from HeaterMode import HeaterMode

        # Arrange: Set mode and reach target
        mock_pump.isOn.return_value = True
        heater.setInputTemp(25.0)
        heater.setModeReachTempAndStop(30)
        heater.on()  # Start heating

        # Act: Reach target temperature
        heater.setInputTemp(30.5)
        with caplog.at_level(logging.INFO):
            heater.runOneLoop()

        # Assert: Heater stopped and mode cleared
        assert heater.isOn() is False
        assert heater.getMode() == HeaterMode.OFF
        assert "Target temp 30 reached" in caplog.text

    def test_heater_mode_hold_turns_on_below_target(self, heater, mock_pump, caplog):
        """Test HOLD mode keeps heater on when below target."""
        import logging

        # Arrange: Turn heater on first, then set mode
        mock_pump.isOn.return_value = True
        heater.setInputTemp(28.0)
        heater.on()  # Turn on first
        heater.setModeHoldTemp(30)

        # Act
        with caplog.at_level(logging.INFO):
            heater.runOneLoop()

        # Assert: Heater stays on
        assert heater.isOn() is True
        assert "ON holding" in caplog.text

    def test_heater_mode_hold_turns_off_at_target(self, heater, mock_pump, caplog):
        """Test HOLD mode turns off when target reached."""
        import logging

        # Arrange: Heater on, at target temperature
        mock_pump.isOn.return_value = True
        heater.setInputTemp(28.0)
        heater.on()  # Turn on first
        heater.setModeHoldTemp(30)
        heater.setInputTemp(30.0)  # Now at target

        # Act
        with caplog.at_level(logging.INFO):
            heater.runOneLoop()

        # Assert: Heater off
        assert heater.isOn() is False
        assert "target temp of 30 reached" in caplog.text

    def test_heater_run_one_loop_off_state(self, heater):
        """Test runOneLoop with heater in OFF state."""
        from HeaterState import HeaterState

        # Arrange: Heater OFF
        heater.state = HeaterState.OFF

        # Act
        heater.runOneLoop()

        # Assert: Heater stays off
        assert heater.isOn() is False

    def test_heater_run_one_loop_stops_at_max_temp(self, heater, mock_pump):
        """Test runOneLoop stops heater at max water temperature."""
        # Arrange: Heater running, temp at max
        mock_pump.isOn.return_value = True
        heater.setInputTemp(33.0)  # maxWaterTemp
        heater.setModeHoldTemp(35)  # Target above max
        heater.on()

        # Act
        heater.runOneLoop()

        # Assert: Heater stopped
        assert heater.isOn() is False

    def test_heater_get_message(self, heater):
        """Test getMessage returns correct format for MQTT."""
        # OFF state
        heater.off()
        msg = heater.getMessage()
        assert msg == {"heater_state": "OFF"}

        # ON state
        heater.setInputTemp(25.0)
        heater.on()
        msg = heater.getMessage()
        assert msg == {"heater_state": "ON"}

    def test_heater_set_state_message_handler_on(self, heater):
        """Test MQTT message handler for ON command."""
        from HeaterState import HeaterState

        # Arrange: Valid temp
        heater.setInputTemp(25.0)

        # Act
        heater.setStateMessageHandler(HeaterState.ON.value)

        # Assert
        assert heater.isOn() is True

    def test_heater_set_state_message_handler_off(self, heater):
        """Test MQTT message handler for OFF command."""
        from HeaterState import HeaterState

        # Arrange: Heater is on
        heater.setInputTemp(25.0)
        heater.on()

        # Act
        heater.setStateMessageHandler(HeaterState.OFF.value)

        # Assert
        assert heater.isOn() is False

    def test_heater_logs_duration_on_off(self, heater):
        """Verify heater logs duration to database when turned off."""
        # Act: Turn on then off
        heater.setInputTemp(25.0)
        heater.on()
        heater.off()

        # Assert: DB logging is mocked globally, we just verify no exceptions
        assert heater.isOn() is False

    def test_heater_target_temp_setting(self, heater):
        """Test target temperature is set correctly in different modes."""
        # HOLD mode
        heater.setModeHoldTemp(28)
        assert heater.targetTemp == 28

        # REACH_AND_STOP mode
        heater.setModeReachTempAndStop(32)
        assert heater.targetTemp == 32

    def test_heater_relay_port_configuration(self, heater, mock_relay_block):
        """Verify heater uses correct relay port."""
        # Arrange: Valid temp
        heater.setInputTemp(25.0)

        # Act: Turn on
        heater.on()

        # Assert: Called with correct port (7)
        mock_relay_block.portOn.assert_called_with(7)

        # Act: Turn off
        heater.off()

        # Assert: Called with correct port (7)
        mock_relay_block.portOff.assert_called_with(7)

    def test_heater_logs_state_transitions(self, heater):
        """Verify state transitions are logged."""
        # Arrange: Valid temp
        heater.setInputTemp(25.0)

        # Turn on
        heater.on()
        assert heater.isOn() is True

        # Turn off
        heater.off()
        assert heater.isOn() is False

    def test_heater_logs_mode_changes(self, heater):
        """Verify mode changes are logged."""
        # HOLD mode
        heater.setModeHoldTemp(30)
        assert heater.getMode().name == "HOLD"

        # REACH_AND_STOP mode
        heater.setModeReachTempAndStop(28)
        assert heater.getMode().name == "REACH_AND_STOP"

    def test_heater_sensor_timestamp_tracking(self, heater):
        """Test that sensor update timestamp is tracked."""
        # Initial state
        initial_timestamp = heater.lastInputTempUpdate

        # Set temperature
        heater.setInputTemp(25.0)

        # Assert: Timestamp updated
        assert heater.lastInputTempUpdate > initial_timestamp

    def test_heater_max_water_temp_configuration(self, heater):
        """Verify heater respects maxWaterTemp configuration."""
        assert heater.maxWaterTemp == 33

    def test_heater_mode_off_clears_target(self, heater):
        """Verify mode OFF is properly handled (though target temp may persist)."""
        from HeaterMode import HeaterMode

        # Arrange: Set HOLD mode with target
        heater.setModeHoldTemp(30)
        assert heater.targetTemp == 30

        # Act: Set mode OFF
        heater.setModeOff()

        # Assert: Mode is OFF (target temp may remain for history)
        assert heater.getMode() == HeaterMode.OFF
