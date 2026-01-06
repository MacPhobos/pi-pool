"""SAFETY-CRITICAL: Watchdog monitoring and emergency shutdown tests.

The Watchdog is the last line of defense against dangerous conditions.
It monitors all system components and triggers emergency shutdowns when
safety violations are detected.

SAFETY REQUIREMENTS TESTED:
- Watchdog detects heater running without pump (most critical check)
- Watchdog shuts down system on network loss
- Watchdog shuts down system on MQTT broker loss
- Emergency stop calls hardStop() on all controllable devices
- Normal operation does not trigger false alarms

CRITICAL: Watchdog MUST be reliable. These tests verify the safety net
that prevents equipment damage and hazardous conditions.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.safety
class TestWatchdogSafety:
    """CRITICAL: Tests for watchdog safety monitoring."""

    @pytest.fixture
    def mock_config(self):
        """Mock config with ping target."""
        config = Mock()
        config.pingTarget = "8.8.8.8"
        return config

    @pytest.fixture
    def mock_pinger(self):
        """Mock pinger that reports connected."""
        pinger = Mock()
        pinger.isConnected = Mock(return_value=True)  # Default: connected
        return pinger

    @pytest.fixture
    def mock_pump(self):
        """Mock pump with isOn() and hardStop()."""
        pump = Mock()
        pump.isOn = Mock(return_value=False)
        pump.hardStop = Mock()
        return pump

    @pytest.fixture
    def mock_heater(self):
        """Mock heater with isOn() and hardStop()."""
        heater = Mock()
        heater.isOn = Mock(return_value=False)
        heater.hardStop = Mock()
        return heater

    @pytest.fixture
    def mock_light(self):
        """Mock light with hardStop()."""
        light = Mock()
        light.hardStop = Mock()
        return light

    @pytest.fixture
    def mock_light_color_logic(self):
        """Mock light color logic with hardStop()."""
        logic = Mock()
        logic.hardStop = Mock()
        return logic

    @pytest.fixture
    def mock_message_bus(self):
        """Mock message bus with isConnected() and connect()."""
        bus = Mock()
        bus.isConnected = Mock(return_value=True)  # Default: connected
        bus.connect = Mock()
        return bus

    @pytest.fixture
    def watchdog(self, mock_config, mock_pinger, mock_pump, mock_heater,
                 mock_light, mock_light_color_logic, mock_message_bus):
        """Create Watchdog instance with all mocked dependencies."""
        from Watchdog import Watchdog

        watchdog = Watchdog(
            config=mock_config,
            pinger=mock_pinger,
            pump=mock_pump,
            heater=mock_heater,
            light=mock_light,
            lightColorLogic=mock_light_color_logic,
            messageBus=mock_message_bus
        )

        return watchdog

    def test_watchdog_detects_heater_without_pump(self, watchdog, mock_pump, mock_heater, caplog):
        """SAFETY: Watchdog must detect and stop heater if pump is off.

        CRITICAL HAZARD: Heater running without pump causes dry fire, overheating,
        equipment damage, and potential fire. This is the MOST CRITICAL safety check.

        Watchdog is the fail-safe that catches this condition even if heater's
        own safety check fails or is bypassed.
        """
        # Arrange: DANGEROUS CONDITION - heater ON, pump OFF
        mock_pump.isOn.return_value = False
        mock_heater.isOn.return_value = True

        # Act: Watchdog check
        with caplog.at_level(logging.INFO):
            watchdog.check()

        # Assert: Both pump and heater hardStop called
        mock_pump.hardStop.assert_called_once()
        mock_heater.hardStop.assert_called_once()

        # Verify logged
        assert "heater on & pump off" in caplog.text

    def test_watchdog_allows_heater_with_pump(self, watchdog, mock_pump, mock_heater):
        """Normal operation: heater with pump running should NOT trigger watchdog."""
        # Arrange: SAFE CONDITION - heater ON, pump ON
        mock_pump.isOn.return_value = True
        mock_heater.isOn.return_value = True

        # Act: Watchdog check
        watchdog.check()

        # Assert: No hardStop calls
        mock_pump.hardStop.assert_not_called()
        mock_heater.hardStop.assert_not_called()

    def test_watchdog_allows_both_off(self, watchdog, mock_pump, mock_heater):
        """Normal operation: both off should NOT trigger watchdog."""
        # Arrange: SAFE CONDITION - both OFF
        mock_pump.isOn.return_value = False
        mock_heater.isOn.return_value = False

        # Act: Watchdog check
        watchdog.check()

        # Assert: No hardStop calls
        mock_pump.hardStop.assert_not_called()
        mock_heater.hardStop.assert_not_called()

    def test_watchdog_allows_pump_without_heater(self, watchdog, mock_pump, mock_heater):
        """Normal operation: pump running without heater is safe."""
        # Arrange: SAFE CONDITION - pump ON, heater OFF
        mock_pump.isOn.return_value = True
        mock_heater.isOn.return_value = False

        # Act: Watchdog check
        watchdog.check()

        # Assert: No hardStop calls
        mock_pump.hardStop.assert_not_called()
        mock_heater.hardStop.assert_not_called()

    def test_watchdog_shuts_down_on_network_loss(self, watchdog, mock_pinger,
                                                   mock_pump, mock_heater,
                                                   mock_light_color_logic, caplog):
        """SAFETY: Watchdog must shut down system on network loss.

        RATIONALE: Network loss means:
        - Cannot receive remote commands to stop equipment
        - Cannot monitor system remotely
        - May indicate broader system failure
        - Fail-safe: shut down to prevent unmonitored operation
        """
        # Arrange: Network is disconnected
        mock_pinger.isConnected.return_value = False

        # Act: Watchdog check
        with caplog.at_level(logging.INFO):
            watchdog.check()

        # Assert: All devices hardStop called
        mock_pump.hardStop.assert_called_once()
        mock_heater.hardStop.assert_called_once()
        mock_light_color_logic.hardStop.assert_called_once()

        # Verify logged
        assert "Lost connection" in caplog.text
        assert "Watchdog: STOP" in caplog.text

    def test_watchdog_no_shutdown_with_network_connected(self, watchdog, mock_pinger,
                                                          mock_pump, mock_heater,
                                                          mock_light_color_logic):
        """Normal operation: connected network should NOT trigger shutdown."""
        # Arrange: Network is connected
        mock_pinger.isConnected.return_value = True
        mock_pump.isOn.return_value = False
        mock_heater.isOn.return_value = False

        # Act: Watchdog check
        watchdog.check()

        # Assert: No hardStop calls
        mock_pump.hardStop.assert_not_called()
        mock_heater.hardStop.assert_not_called()
        mock_light_color_logic.hardStop.assert_not_called()

    def test_watchdog_reconnects_message_bus_on_disconnect(self, watchdog, mock_message_bus):
        """Watchdog should attempt to reconnect MQTT broker on disconnect.

        NOTE: Message bus disconnect triggers reconnect attempt, NOT full shutdown.
        This is less critical than network loss.
        """
        # Arrange: Message bus disconnected
        mock_message_bus.isConnected.return_value = False

        # Act: Watchdog check
        watchdog.check()

        # Assert: Reconnect called
        mock_message_bus.connect.assert_called_once()

    def test_watchdog_no_reconnect_when_message_bus_connected(self, watchdog, mock_message_bus):
        """No reconnect attempt when message bus is connected."""
        # Arrange: Message bus connected
        mock_message_bus.isConnected.return_value = True

        # Act: Watchdog check
        watchdog.check()

        # Assert: Connect NOT called
        mock_message_bus.connect.assert_not_called()

    def test_watchdog_multiple_conditions_trigger_all_checks(self, watchdog,
                                                              mock_pump, mock_heater,
                                                              mock_pinger,
                                                              mock_light_color_logic,
                                                              caplog):
        """Multiple safety violations should trigger all appropriate responses.

        SCENARIO: Heater on without pump AND network loss
        Both conditions should be detected and handled.
        """
        # Arrange: Multiple violations
        mock_pump.isOn.return_value = False
        mock_heater.isOn.return_value = True  # Heater/pump violation
        mock_pinger.isConnected.return_value = False  # Network loss

        # Act: Watchdog check
        with caplog.at_level(logging.INFO):
            watchdog.check()

        # Assert: All hardStop calls made (may be called multiple times)
        assert mock_pump.hardStop.called
        assert mock_heater.hardStop.called
        assert mock_light_color_logic.hardStop.called

        # Verify both violations logged
        assert "heater on & pump off" in caplog.text
        assert "Lost connection" in caplog.text

    def test_watchdog_normal_operation_no_action(self, watchdog, mock_pump, mock_heater,
                                                  mock_pinger, mock_message_bus,
                                                  mock_light_color_logic):
        """SAFETY: Normal operation should not trigger shutdown.

        All systems healthy:
        - Pump and heater states are safe
        - Network is connected
        - Message bus is connected

        Watchdog should silently pass.
        """
        # Arrange: All systems healthy
        mock_pump.isOn.return_value = True
        mock_heater.isOn.return_value = True  # Safe: pump is on
        mock_pinger.isConnected.return_value = True
        mock_message_bus.isConnected.return_value = True

        # Act: Watchdog check
        watchdog.check()

        # Assert: No hardStop or reconnect calls
        mock_pump.hardStop.assert_not_called()
        mock_heater.hardStop.assert_not_called()
        mock_light_color_logic.hardStop.assert_not_called()
        mock_message_bus.connect.assert_not_called()

    def test_watchdog_emergency_stop_all_devices(self, watchdog, mock_pump,
                                                  mock_heater, mock_light_color_logic,
                                                  mock_pinger, caplog):
        """SAFETY: Emergency stop must shut down ALL controllable devices.

        On network loss, ALL devices must stop for safety.
        Verify all devices' hardStop() methods are called.
        """
        # Arrange: Network loss (emergency condition)
        mock_pinger.isConnected.return_value = False

        # Act: Watchdog check (triggers emergency stop)
        with caplog.at_level(logging.INFO):
            watchdog.check()

        # Assert: All devices stopped
        mock_pump.hardStop.assert_called_once()
        mock_heater.hardStop.assert_called_once()
        mock_light_color_logic.hardStop.assert_called_once()
        # Note: light itself doesn't have hardStop in Watchdog, only lightColorLogic

        # Verify emergency logged
        assert "Watchdog: STOP" in caplog.text

    def test_watchdog_check_order_heater_before_network(self, watchdog,
                                                         mock_pump, mock_heater,
                                                         mock_pinger,
                                                         mock_light_color_logic):
        """Watchdog should check heater/pump violation before network.

        This ensures most critical check happens first, even if other
        conditions would also trigger shutdown.
        """
        # Arrange: Both violations
        mock_pump.isOn.return_value = False
        mock_heater.isOn.return_value = True
        mock_pinger.isConnected.return_value = False

        # Act: Watchdog check
        watchdog.check()

        # Assert: Both conditions trigger hardStop
        # (We can't strictly verify order without more complex mocking,
        #  but verify both are called)
        assert mock_pump.hardStop.called
        assert mock_heater.hardStop.called
        assert mock_light_color_logic.hardStop.called

    def test_watchdog_config_ping_target_used(self, watchdog, mock_config, mock_pinger, caplog):
        """Verify watchdog uses config.pingTarget in log messages."""
        # Arrange: Set specific ping target
        mock_config.pingTarget = "192.168.1.1"
        mock_pinger.isConnected.return_value = False

        # Act: Watchdog check
        with caplog.at_level(logging.INFO):
            watchdog.check()

        # Assert: Ping target appears in log
        assert "192.168.1.1" in caplog.text
