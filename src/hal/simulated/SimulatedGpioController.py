"""Simulated GPIO controller for testing without hardware."""
import logging
from typing import Dict
from hal.interfaces import IGpioController, PinMode, PinState, PinDirection


class SimulatedGpioController(IGpioController):
    """Simulated GPIO controller implementation for testing without hardware."""

    def __init__(self):
        """Initialize the simulated GPIO controller."""
        self.pinStates: Dict[int, PinState] = {}
        self.pinDirections: Dict[int, PinDirection] = {}
        self.mode: PinMode = PinMode.BCM
        logging.info("SimulatedGpioController: Initialized")

    def setMode(self, mode: PinMode) -> None:
        """Set GPIO pin numbering mode (BCM or BOARD)."""
        self.mode = mode
        logging.info(f"SimulatedGpioController: Set mode to {mode.value}")

    def setup(self, pin: int, direction: PinDirection) -> None:
        """Configure a GPIO pin as input or output."""
        self.pinDirections[pin] = direction
        # Initialize output pins to LOW state
        if direction == PinDirection.OUT:
            self.pinStates[pin] = PinState.LOW
        logging.info(f"SimulatedGpioController: Setup pin {pin} as {direction.value}")

    def output(self, pin: int, state: PinState) -> None:
        """Set the output state of a GPIO pin."""
        if pin not in self.pinDirections:
            logging.warning(f"SimulatedGpioController: Pin {pin} not configured, setting up as OUTPUT")
            self.setup(pin, PinDirection.OUT)
        elif self.pinDirections[pin] != PinDirection.OUT:
            logging.error(f"SimulatedGpioController: Cannot output to input pin {pin}")
            raise ValueError(f"Pin {pin} is configured as INPUT")

        self.pinStates[pin] = state
        logging.info(f"SimulatedGpioController: Set pin {pin} to {state.value}")

    def input(self, pin: int) -> PinState:
        """Read the input state of a GPIO pin."""
        if pin not in self.pinStates:
            logging.warning(f"SimulatedGpioController: Pin {pin} not initialized, returning LOW")
            return PinState.LOW

        state = self.pinStates[pin]
        logging.info(f"SimulatedGpioController: Read pin {pin} as {state.value}")
        return state

    def cleanup(self) -> None:
        """Release GPIO resources."""
        self.pinStates.clear()
        self.pinDirections.clear()
        logging.info("SimulatedGpioController: Cleanup completed")

    def getPinState(self, pin: int) -> PinState:
        """Get current pin state (helper for testing).

        Args:
            pin: Pin number

        Returns:
            Current pin state or LOW if not set
        """
        return self.pinStates.get(pin, PinState.LOW)
