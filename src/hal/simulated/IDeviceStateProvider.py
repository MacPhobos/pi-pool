"""
IDeviceStateProvider.py - Abstract interface for querying device states
"""

from abc import ABC, abstractmethod


class IDeviceStateProvider(ABC):
    """Abstract interface for providing device state information to simulation.

    This allows the thermal simulation to query the current state of pool devices
    (pump, heater, light) without creating tight coupling to specific implementations.
    """

    @abstractmethod
    def isHeaterOn(self) -> bool:
        """Check if the heater is currently running.

        Returns:
            True if heater is ON, False otherwise
        """
        pass

    @abstractmethod
    def isPumpOn(self) -> bool:
        """Check if the pump is currently running.

        Returns:
            True if pump is ON, False otherwise
        """
        pass

    @abstractmethod
    def isLightOn(self) -> bool:
        """Check if the pool light is currently ON.

        Returns:
            True if light is ON, False otherwise
        """
        pass
