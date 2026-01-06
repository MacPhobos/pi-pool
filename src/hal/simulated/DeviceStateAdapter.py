"""
DeviceStateAdapter.py - Adapter to query device states for simulation
"""

from .IDeviceStateProvider import IDeviceStateProvider


class DeviceStateAdapter(IDeviceStateProvider):
    """Adapter that provides device state information to thermal simulation.

    This adapter queries the actual Pump, Heater, and Light objects to determine
    their current operational state, allowing the simulation to respond to device
    state changes.

    Attributes:
        pump: Pump instance to query
        heater: Heater instance to query
        light: Light instance to query
    """

    def __init__(self, pump, heater, light):
        """Initialize adapter with device references.

        Args:
            pump: Pump instance (must have isOn() method)
            heater: Heater instance (must have isOn() method)
            light: Light instance (must have isOn() method)
        """
        self.pump = pump
        self.heater = heater
        self.light = light

    def isHeaterOn(self) -> bool:
        """Check if the heater is currently running.

        Returns:
            True if heater is ON, False otherwise
        """
        return self.heater.isOn() if self.heater else False

    def isPumpOn(self) -> bool:
        """Check if the pump is currently running.

        Returns:
            True if pump is ON, False otherwise
        """
        return self.pump.isOn() if self.pump else False

    def isLightOn(self) -> bool:
        """Check if the pool light is currently ON.

        Returns:
            True if light is ON, False otherwise
        """
        return self.light.isOn() if self.light else False
