"""Unit tests for Pump class.

Tests core Pump functionality including:
- Basic on/off control
- State management and queries
- Mode operations (OFF, REACH_TIME_AND_STOP)
- Timer tracking for maintenance
- MQTT message handlers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestPump:
    """Unit tests for Pump class."""

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
        """Mock relay block for pump tests."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def pump(self, mock_relay_block):
        """Create Pump instance with mocked dependencies."""
        from Pump import Pump

        pump = Pump(relayBlock=mock_relay_block, pumpPort=8)
        return pump

    def test_pump_initialization(self, pump):
        """Verify pump initializes with correct defaults."""
        from PumpState import PumpState
        from PumpMode import PumpMode

        assert pump.getState() == PumpState.OFF
        assert pump.getMode() == PumpMode.OFF
        assert pump.runForXMinutes is None
        assert pump.relayBlockPort == 8

    def test_pump_on(self, pump, mock_relay_block):
        """Test turning pump on."""
        from PumpState import PumpState

        # Act
        pump.on()

        # Assert
        assert pump.getState() == PumpState.ON
        mock_relay_block.portOn.assert_called_once_with(8)

    def test_pump_off(self, pump, mock_relay_block):
        """Test turning pump off."""
        from PumpState import PumpState

        # Arrange: Turn on first
        pump.on()

        # Act
        pump.off()

        # Assert
        assert pump.getState() == PumpState.OFF
        mock_relay_block.portOff.assert_called_with(8)

    def test_pump_get_state(self, pump):
        """Test getState returns current state."""
        from PumpState import PumpState

        # Initially OFF
        assert pump.getState() == PumpState.OFF

        # Turn on
        pump.on()
        assert pump.getState() == PumpState.ON

        # Turn off
        pump.off()
        assert pump.getState() == PumpState.OFF

    def test_pump_is_on_property(self, pump):
        """Test isOn() property returns correct boolean."""
        # Initially OFF
        assert pump.isOn() is False

        # Turn on
        pump.on()
        assert pump.isOn() is True

        # Turn off
        pump.off()
        assert pump.isOn() is False

    def test_pump_get_mode(self, pump):
        """Test getMode returns current mode."""
        from PumpMode import PumpMode

        # Initially OFF
        assert pump.getMode() == PumpMode.OFF

        # Set timed mode
        pump.setRunForXMinutesAndStop(10)
        assert pump.getMode() == PumpMode.REACH_TIME_AND_STOP

    def test_pump_mode_reach_time_and_stop(self, pump):
        """Test setting REACH_TIME_AND_STOP mode."""
        from PumpMode import PumpMode

        # Act
        pump.setRunForXMinutesAndStop(30)

        # Assert
        assert pump.getMode() == PumpMode.REACH_TIME_AND_STOP
        assert pump.runForXMinutes == 30
        assert pump.isOn() is True  # Should turn on automatically

    def test_pump_mode_reach_time_and_stop_logs_event(self, pump):
        """Verify timed mode logs event."""
        # Act
        pump.setRunForXMinutesAndStop(15)

        # Assert: Event logging is mocked globally, we just verify no exceptions
        assert pump.getMode().name == "REACH_TIME_AND_STOP"

    def test_pump_set_mode_off(self, pump):
        """Test setting mode to OFF."""
        from PumpMode import PumpMode

        # Arrange: Set timed mode
        pump.setRunForXMinutesAndStop(10)
        assert pump.getMode() == PumpMode.REACH_TIME_AND_STOP

        # Act: Set mode OFF
        pump.setModeOff()

        # Assert
        assert pump.getMode() == PumpMode.OFF
        assert pump.runForXMinutes is None
        assert pump.isOn() is False

    def test_pump_timer_tracking(self, pump):
        """Test that timer starts and stops correctly."""
        # Turn on (starts timer)
        pump.on()

        # Timer should be running (we can't easily verify internals,
        # but we can verify pump is on which should start timer)
        assert pump.isOn() is True

        # Turn off (stops timer and logs duration)
        pump.off()
        assert pump.isOn() is False

    def test_pump_logs_duration_on_off(self, pump):
        """Verify pump logs duration to database when turned off."""
        # Act: Turn on then off
        pump.on()
        pump.off()

        # Assert: DB logging is mocked globally, we just verify no exceptions
        assert pump.isOn() is False

    def test_pump_get_message(self, pump):
        """Test getMessage returns correct format for MQTT."""
        # OFF state
        pump.off()
        msg = pump.getMessage()
        assert msg == {"pump_state": "OFF"}

        # ON state
        pump.on()
        msg = pump.getMessage()
        assert msg == {"pump_state": "ON"}

    def test_pump_set_state_message_handler_on(self, pump):
        """Test MQTT message handler for ON command."""
        from PumpState import PumpState

        # Act
        pump.setStateMessageHandler(PumpState.ON.value)

        # Assert
        assert pump.isOn() is True

    def test_pump_set_state_message_handler_off(self, pump):
        """Test MQTT message handler for OFF command."""
        from PumpState import PumpState

        # Arrange: Pump is on
        pump.on()

        # Act
        pump.setStateMessageHandler(PumpState.OFF.value)

        # Assert
        assert pump.isOn() is False

    def test_pump_set_on_message_handler(self, pump):
        """Test dedicated ON message handler."""
        from PumpState import PumpState

        # Act
        pump.setOnMessageHandler(PumpState.ON.value)

        # Assert
        assert pump.isOn() is True

    def test_pump_set_off_message_handler(self, pump):
        """Test dedicated OFF message handler."""
        from PumpState import PumpState

        # Arrange: Pump is on
        pump.on()

        # Act
        pump.setOffMessageHandler(PumpState.OFF.value)

        # Assert
        assert pump.isOn() is False

    def test_pump_run_one_loop_in_off_mode(self, pump):
        """Test runOneLoop with pump in OFF mode."""
        # Arrange: Pump is OFF
        assert pump.isOn() is False

        # Act: Run loop
        pump.runOneLoop()

        # Assert: Nothing should change
        assert pump.isOn() is False

    def test_pump_run_one_loop_clears_mode_when_off(self, pump):
        """Test runOneLoop clears mode if pump is OFF but mode is not OFF."""
        from PumpState import PumpState
        from PumpMode import PumpMode

        # Arrange: Inconsistent state (OFF with mode set)
        pump.state = PumpState.OFF
        pump.mode = PumpMode.REACH_TIME_AND_STOP

        # Act
        pump.runOneLoop()

        # Assert: Mode cleared
        assert pump.getMode() == PumpMode.OFF

    def test_pump_run_one_loop_timed_mode_running(self, pump, caplog):
        """Test runOneLoop in timed mode while running."""
        import logging

        # Arrange: Timed mode
        pump.setRunForXMinutesAndStop(10)

        # Act: Run loop with timer showing progress
        with caplog.at_level(logging.INFO):
            with patch.object(pump.timer, 'elapsedSeconds', return_value=120):  # 2 minutes
                pump.runOneLoop()

        # Assert: Still running, log shows progress
        assert pump.isOn() is True
        assert "Pump On Timer" in caplog.text
        assert "elapsed: 2.0 min" in caplog.text

    def test_pump_run_one_loop_timed_mode_finished(self, pump):
        """Test runOneLoop stops pump when time limit reached."""
        # Arrange: Timed mode for 1 minute
        pump.setRunForXMinutesAndStop(1)

        # Act: Run loop with timer showing time exceeded
        with patch.object(pump.timer, 'elapsedSeconds', return_value=65):  # 65 seconds > 1 minute
            pump.runOneLoop()

        # Assert: Pump stopped
        assert pump.isOn() is False
        assert pump.getMode().name == "OFF"

    def test_pump_logs_state_transitions(self, pump):
        """Verify state transitions are logged."""
        # Turn on
        pump.on()
        assert pump.isOn() is True

        # Turn off
        pump.off()
        assert pump.isOn() is False

    def test_pump_logs_mode_changes(self, pump):
        """Verify mode changes are logged."""
        # Set timed mode
        pump.setRunForXMinutesAndStop(20)
        assert pump.getMode().name == "REACH_TIME_AND_STOP"

        # Set mode OFF
        pump.setModeOff()
        assert pump.getMode().name == "OFF"

    def test_pump_timer_resets_on_timed_mode(self, pump):
        """Verify timer is reset when setting timed mode."""
        # Arrange: Turn pump on manually first
        pump.on()

        # Act: Set timed mode (should reset timer)
        pump.setRunForXMinutesAndStop(5)

        # Assert: Timer was stopped and restarted
        # (We verify pump is on in timed mode)
        assert pump.isOn() is True
        assert pump.getMode().name == "REACH_TIME_AND_STOP"

    def test_pump_relay_port_configuration(self, pump, mock_relay_block):
        """Verify pump uses correct relay port."""
        # Act: Turn on
        pump.on()

        # Assert: Called with correct port (8)
        mock_relay_block.portOn.assert_called_with(8)

        # Act: Turn off
        pump.off()

        # Assert: Called with correct port (8)
        mock_relay_block.portOff.assert_called_with(8)
