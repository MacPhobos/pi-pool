"""Real GPIO controller using RPi.GPIO library."""
import logging
from hal.interfaces import IGpioController, PinMode, PinState, PinDirection


class RealGpioController(IGpioController):
    """Real hardware GPIO controller implementation using RPi.GPIO."""

    def __init__(self):
        """Initialize the real GPIO controller."""
        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO
            logging.info("RealGpioController: Initialized with RPi.GPIO")
        except ImportError as e:
            logging.error(f"RealGpioController: Failed to import RPi.GPIO: {e}")
            raise RuntimeError("RPi.GPIO not available - cannot use RealGpioController") from e

    def setMode(self, mode: PinMode) -> None:
        """Set GPIO pin numbering mode (BCM or BOARD)."""
        if mode == PinMode.BCM:
            self._GPIO.setmode(self._GPIO.BCM)
            logging.info("RealGpioController: Set mode to BCM")
        elif mode == PinMode.BOARD:
            self._GPIO.setmode(self._GPIO.BOARD)
            logging.info("RealGpioController: Set mode to BOARD")
        else:
            raise ValueError(f"Invalid pin mode: {mode}")

    def setup(self, pin: int, direction: PinDirection) -> None:
        """Configure a GPIO pin as input or output."""
        if direction == PinDirection.OUT:
            self._GPIO.setup(pin, self._GPIO.OUT)
            logging.info(f"RealGpioController: Setup pin {pin} as OUTPUT")
        elif direction == PinDirection.IN:
            self._GPIO.setup(pin, self._GPIO.IN)
            logging.info(f"RealGpioController: Setup pin {pin} as INPUT")
        else:
            raise ValueError(f"Invalid pin direction: {direction}")

    def output(self, pin: int, state: PinState) -> None:
        """Set the output state of a GPIO pin."""
        if state == PinState.HIGH:
            self._GPIO.output(pin, self._GPIO.HIGH)
        elif state == PinState.LOW:
            self._GPIO.output(pin, self._GPIO.LOW)
        else:
            raise ValueError(f"Invalid pin state: {state}")

    def input(self, pin: int) -> PinState:
        """Read the input state of a GPIO pin."""
        value = self._GPIO.input(pin)
        return PinState.HIGH if value == self._GPIO.HIGH else PinState.LOW

    def cleanup(self) -> None:
        """Release GPIO resources."""
        self._GPIO.cleanup()
        logging.info("RealGpioController: GPIO cleanup completed")
