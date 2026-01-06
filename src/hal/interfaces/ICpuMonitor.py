"""CPU monitor interface for hardware abstraction."""
from abc import ABC, abstractmethod


class ICpuMonitor(ABC):
    """Interface for CPU temperature monitoring."""

    @abstractmethod
    def getTemperature(self) -> float:
        """Get current CPU temperature in Celsius.

        Returns:
            CPU temperature in Celsius
        """
        pass
