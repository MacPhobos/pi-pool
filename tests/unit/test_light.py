"""Unit tests for Light class.

Tests the Light class for pool light control.
"""

import pytest
import time
from unittest.mock import Mock
from Light import Light
from LightState import LightState
from hal.interfaces import PinState


@pytest.mark.unit
class TestLight:
    """Unit tests for Light class functionality."""

    @pytest.fixture
    def light(self, config, mock_relay_block):
        """Provide Light instance with mock relay block."""
        return Light(mock_relay_block, lightPort=6)

    def test_light_initial_state_off(self, config, mock_relay_block):
        """Light should initialize in OFF state."""
        light = Light(mock_relay_block, lightPort=6)

        assert light.state == LightState.OFF
        assert light.getState() == LightState.OFF
        assert light.isOn() is False
        assert light.relayBlockPort == 6

        # Verify GPIO state (port 6 = GPIO 23, should be HIGH for OFF)
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.HIGH

    def test_light_on(self, light, mock_relay_block):
        """Turning light ON should activate relay and update state."""
        light.on()

        assert light.state == LightState.ON
        assert light.getState() == LightState.ON
        assert light.isOn() is True
        assert light.lastOnTime is not None

        # Verify GPIO state (port 6 = GPIO 23, should be LOW for ON)
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.LOW

    def test_light_off(self, light, mock_relay_block):
        """Turning light OFF should deactivate relay and update state."""
        light.on()
        light.off()

        assert light.state == LightState.OFF
        assert light.getState() == LightState.OFF
        assert light.isOn() is False
        assert light.lastOffTime is not None

        # Verify GPIO state (port 6 = GPIO 23, should be HIGH for OFF)
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.HIGH

    def test_light_toggle_on_then_off(self, light, mock_relay_block):
        """Light should toggle between ON and OFF states."""
        # Start OFF
        assert light.isOn() is False

        # Turn ON
        light.on()
        assert light.isOn() is True

        # Turn OFF
        light.off()
        assert light.isOn() is False

    def test_light_get_state(self, light):
        """getState should return current LightState."""
        assert light.getState() == LightState.OFF

        light.on()
        assert light.getState() == LightState.ON

    def test_light_get_message(self, light):
        """getMessage should return status dictionary."""
        message = light.getMessage()

        assert "light_state" in message
        assert message["light_state"] == LightState.OFF.value

        light.on()
        message = light.getMessage()
        assert message["light_state"] == LightState.ON.value

    def test_light_seconds_in_off_state(self, light):
        """secondsInOffState should track time in OFF state."""
        # Initial state: OFF
        time.sleep(0.05)
        seconds_off = light.secondsInOffState()

        assert seconds_off >= 0.05

        # Turn ON
        light.on()
        seconds_off = light.secondsInOffState()
        assert seconds_off == 0  # Should return 0 when ON

    def test_light_seconds_in_off_state_after_on_off_cycle(self, light):
        """secondsInOffState should update after ON/OFF cycle."""
        # Turn ON
        light.on()
        assert light.secondsInOffState() == 0

        # Turn OFF
        light.off()
        time.sleep(0.05)

        seconds_off = light.secondsInOffState()
        assert seconds_off >= 0.05

    def test_light_set_state_message_handler_on(self, light, mock_relay_block):
        """setStateMessageHandler should turn light ON for 'ON' message."""
        light.setStateMessageHandler("ON")

        assert light.state == LightState.ON
        # Verify GPIO state
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.LOW

    def test_light_set_state_message_handler_off(self, light, mock_relay_block):
        """setStateMessageHandler should turn light OFF for 'OFF' message."""
        light.on()
        light.setStateMessageHandler("OFF")

        assert light.state == LightState.OFF

    def test_light_set_state_message_handler_invalid(self, light):
        """setStateMessageHandler should ignore invalid messages."""
        light.on()
        initial_state = light.state

        light.setStateMessageHandler("INVALID")

        # State should not change for invalid message
        assert light.state == initial_state

    def test_light_cycle_one(self, light, mock_relay_block):
        """cycleOne should turn light OFF then ON with delay."""
        light.on()

        # cycleOne should turn OFF, delay, then ON
        light.cycleOne(delay=0.01)  # Use short delay for test

        # Should end in ON state
        assert light.state == LightState.ON
        # Verify GPIO is LOW (ON)
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.LOW

    def test_light_cycle_multiple(self, light, mock_relay_block):
        """cycle should perform multiple OFF/ON cycles.

        Note: cycle() runs asynchronously, so we must wait for completion.
        """
        light.on()

        # Perform 3 cycles (runs asynchronously)
        light.cycle(count=3, delay=0.01)

        # Wait for async cycle to complete
        light.waitForCycle(timeout=5)

        # Should end in ON state
        assert light.state == LightState.ON
        # Verify GPIO is LOW (ON)
        gpio_num = mock_relay_block.gpioFromPort(6)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.LOW

    def test_light_cycle_zero_count(self, light, mock_relay_block):
        """cycle with count=0 should do nothing."""
        light.on()
        initial_state = light.state

        light.cycle(count=0, delay=0.01)

        # State should remain ON
        assert light.state == initial_state
        assert light.state == LightState.ON

    def test_light_cycle_negative_count(self, light, mock_relay_block):
        """cycle with negative count should do nothing."""
        light.on()
        initial_state = light.state

        light.cycle(count=-5, delay=0.01)

        # State should remain ON
        assert light.state == initial_state
        assert light.state == LightState.ON

    def test_light_last_on_time_tracked(self, light):
        """Light should track when it was last turned ON."""
        assert light.lastOnTime is None

        before = time.time()
        light.on()
        after = time.time()

        assert light.lastOnTime is not None
        assert before <= light.lastOnTime <= after

    def test_light_last_off_time_tracked(self, light):
        """Light should track when it was last turned OFF."""
        # lastOffTime set during init (calls off())
        initial_off_time = light.lastOffTime

        light.on()
        time.sleep(0.01)

        before = time.time()
        light.off()
        after = time.time()

        assert light.lastOffTime is not None
        assert light.lastOffTime > initial_off_time
        assert before <= light.lastOffTime <= after

    def test_light_with_different_port(self, config, mock_relay_block):
        """Light should work with different relay ports."""
        light = Light(mock_relay_block, lightPort=3)

        assert light.relayBlockPort == 3

        light.on()
        # Verify GPIO for port 3
        gpio_num = mock_relay_block.gpioFromPort(3)
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.LOW

        light.off()
        assert mock_relay_block.gpio.getPinState(gpio_num) == PinState.HIGH
