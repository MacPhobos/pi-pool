"""Unit tests for RelayBlock class.

Tests the RelayBlock GPIO relay interface with simulated GPIO.
"""

import pytest
from RelayBlock import RelayBlock
from hal.interfaces import PinState


@pytest.mark.unit
class TestRelayBlock:
    """Unit tests for RelayBlock GPIO control."""

    def test_relay_block_initialization(self, config, simulated_gpio):
        """RelayBlock should initialize with simulated GPIO and set up pins."""
        relay = RelayBlock(simulated_gpio)

        assert relay.gpio == simulated_gpio
        assert relay.config is not None
        # All pins should be initialized HIGH (relays OFF, active-LOW)
        for pin in relay.pins:
            gpio_num = pin["gpio"]
            state = simulated_gpio.getPinState(gpio_num)
            assert state == PinState.HIGH

    def test_relay_block_gpio_mode_set(self, config, simulated_gpio):
        """RelayBlock should set GPIO mode to BCM."""
        RelayBlock(simulated_gpio)

        # Check that setMode was called (simulated GPIO tracks this)
        assert simulated_gpio.mode is not None

    def test_port_on_activates_gpio(self, config, simulated_gpio):
        """Turning port ON should set GPIO pin LOW (active-LOW relay)."""
        relay = RelayBlock(simulated_gpio)

        # Turn port 8 ON (pump port)
        relay.portOn(8)

        # Port 8 is GPIO 25 (from pins mapping)
        gpio_num = relay.gpioFromPort(8)
        assert gpio_num == 25

        state = simulated_gpio.getPinState(gpio_num)
        assert state == PinState.LOW

    def test_port_off_deactivates_gpio(self, config, simulated_gpio):
        """Turning port OFF should set GPIO pin HIGH (active-LOW relay)."""
        relay = RelayBlock(simulated_gpio)

        # Turn port 8 ON then OFF
        relay.portOn(8)
        relay.portOff(8)

        gpio_num = relay.gpioFromPort(8)
        state = simulated_gpio.getPinState(gpio_num)
        assert state == PinState.HIGH

    def test_gpio_from_port_mapping(self, config, simulated_gpio):
        """RelayBlock should correctly map port numbers to GPIO pins."""
        relay = RelayBlock(simulated_gpio)

        # Test known mappings from pins array
        assert relay.gpioFromPort(8) == 25  # Pump port
        assert relay.gpioFromPort(6) == 23  # Light port (typically)
        assert relay.gpioFromPort(7) == 24  # Heater port (typically)
        assert relay.gpioFromPort(1) == 4
        assert relay.gpioFromPort(2) == 17

    def test_multiple_ports_independent(self, config, simulated_gpio):
        """Multiple ports should operate independently."""
        relay = RelayBlock(simulated_gpio)

        # Turn on port 8 and 7
        relay.portOn(8)
        relay.portOn(7)

        assert simulated_gpio.getPinState(25) == PinState.LOW  # Port 8
        assert simulated_gpio.getPinState(24) == PinState.LOW  # Port 7

        # Turn off only port 8
        relay.portOff(8)

        assert simulated_gpio.getPinState(25) == PinState.HIGH  # Port 8 OFF
        assert simulated_gpio.getPinState(24) == PinState.LOW   # Port 7 still ON

    def test_pin_on_direct(self, config, simulated_gpio):
        """Direct pinOn should set GPIO LOW."""
        relay = RelayBlock(simulated_gpio)

        relay.pinOn(25)

        assert simulated_gpio.getPinState(25) == PinState.LOW

    def test_pin_off_direct(self, config, simulated_gpio):
        """Direct pinOff should set GPIO HIGH."""
        relay = RelayBlock(simulated_gpio)

        relay.pinOn(25)
        relay.pinOff(25)

        assert simulated_gpio.getPinState(25) == PinState.HIGH

    def test_relay_block_with_no_devices_mode(self, config, simulated_gpio, monkeypatch):
        """RelayBlock should respect noDevices config and not switch GPIO."""
        # Set noDevices to True in config
        monkeypatch.setattr(config, 'noDevices', True)

        relay = RelayBlock(simulated_gpio)

        # Attempting to turn on should not change GPIO state
        initial_state = simulated_gpio.getPinState(25)
        relay.portOn(8)
        final_state = simulated_gpio.getPinState(25)

        # State should remain unchanged when noDevices=True
        assert initial_state == final_state

    def test_relay_block_all_pins_initialized(self, config, simulated_gpio):
        """All pins in pins array should be initialized as outputs."""
        relay = RelayBlock(simulated_gpio)

        # Check all 8 pins are initialized HIGH
        for pin in relay.pins:
            gpio_num = pin["gpio"]
            state = simulated_gpio.getPinState(gpio_num)
            assert state == PinState.HIGH

    def test_relay_block_port_toggle(self, config, simulated_gpio):
        """Toggling port ON and OFF should work correctly."""
        relay = RelayBlock(simulated_gpio)
        gpio_num = relay.gpioFromPort(8)

        # Initial state: HIGH (OFF)
        assert simulated_gpio.getPinState(gpio_num) == PinState.HIGH

        # Turn ON
        relay.portOn(8)
        assert simulated_gpio.getPinState(gpio_num) == PinState.LOW

        # Turn OFF
        relay.portOff(8)
        assert simulated_gpio.getPinState(gpio_num) == PinState.HIGH

        # Turn ON again
        relay.portOn(8)
        assert simulated_gpio.getPinState(gpio_num) == PinState.LOW
