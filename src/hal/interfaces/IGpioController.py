"""GPIO controller interface for hardware abstraction."""
from abc import ABC, abstractmethod
from enum import Enum


class PinMode(Enum):
    """GPIO pin numbering mode."""
    BCM = "BCM"
    BOARD = "BOARD"


class PinState(Enum):
    """GPIO pin state (HIGH/LOW)."""
    HIGH = 1
    LOW = 0


class PinDirection(Enum):
    """GPIO pin direction (IN/OUT)."""
    IN = "IN"
    OUT = "OUT"


class IGpioController(ABC):
    """Interface for GPIO pin control operations."""

    @abstractmethod
    def setMode(self, mode: PinMode) -> None:
        """Set GPIO pin numbering mode (BCM or BOARD).

        Args:
            mode: Pin numbering mode to use
        """
        pass

    @abstractmethod
    def setup(self, pin: int, direction: PinDirection) -> None:
        """Configure a GPIO pin as input or output.

        Args:
            pin: Pin number
            direction: Pin direction (IN or OUT)
        """
        pass

    @abstractmethod
    def output(self, pin: int, state: PinState) -> None:
        """Set the output state of a GPIO pin.

        Args:
            pin: Pin number
            state: Pin state (HIGH or LOW)
        """
        pass

    @abstractmethod
    def input(self, pin: int) -> PinState:
        """Read the input state of a GPIO pin.

        Args:
            pin: Pin number

        Returns:
            Current pin state
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release GPIO resources."""
        pass
