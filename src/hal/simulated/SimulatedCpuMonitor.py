"""Simulated CPU monitor for testing without hardware."""
import logging
import random
from hal.interfaces import ICpuMonitor


class SimulatedCpuMonitor(ICpuMonitor):
    """Simulated CPU monitor implementation for testing without hardware."""

    def __init__(self, baseTemperature: float = 50.0, variance: float = 5.0):
        """Initialize the simulated CPU monitor.

        Args:
            baseTemperature: Base CPU temperature in Celsius (default 50°C)
            variance: Random variance range (+/- this value, default 5°C)
        """
        self.baseTemperature = baseTemperature
        self.variance = variance
        logging.info(f"SimulatedCpuMonitor: Initialized with base temperature {baseTemperature:.2f}°C")

    def getTemperature(self) -> float:
        """Get simulated CPU temperature.

        Returns:
            CPU temperature in Celsius (40-60°C range with variance)
        """
        # Generate temperature in realistic range (40-60°C)
        temp = self.baseTemperature + random.uniform(-self.variance, self.variance)

        # Clamp to realistic range
        temp = max(40.0, min(60.0, temp))

        # Format to 2 decimal places
        return round(temp, 2)

    def setBaseTemperature(self, temperature: float) -> None:
        """Set the base temperature for simulation (helper for testing).

        Args:
            temperature: New base temperature in Celsius
        """
        self.baseTemperature = temperature
        logging.info(f"SimulatedCpuMonitor: Set base temperature to {temperature:.2f}°C")
