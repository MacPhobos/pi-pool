"""Temperature sensor interface for hardware abstraction."""
from abc import ABC, abstractmethod
from typing import Tuple


class ITemperatureSensor(ABC):
    """Interface for temperature sensor operations."""

    @abstractmethod
    def readTemperature(self) -> Tuple[str, float]:
        """Read temperature from sensor.

        Returns:
            Tuple of (sensor_name, temperature_celsius)
        """
        pass

    @abstractmethod
    def getName(self) -> str:
        """Get the sensor name.

        Returns:
            Sensor identifier name
        """
        pass

    @abstractmethod
    def isAvailable(self) -> bool:
        """Check if sensor is available/connected.

        Returns:
            True if sensor is available, False otherwise
        """
        pass
