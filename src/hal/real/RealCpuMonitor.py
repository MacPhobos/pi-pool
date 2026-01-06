"""Real CPU monitor using gpiozero library."""
import logging
from hal.interfaces import ICpuMonitor


class RealCpuMonitor(ICpuMonitor):
    """Real hardware CPU monitor implementation using gpiozero."""

    def __init__(self):
        """Initialize the real CPU monitor."""
        try:
            from gpiozero import CPUTemperature
            self._cpu = CPUTemperature()
            logging.info("RealCpuMonitor: Initialized with gpiozero.CPUTemperature")
        except ImportError as e:
            logging.error(f"RealCpuMonitor: Failed to import gpiozero: {e}")
            raise RuntimeError("gpiozero not available - cannot use RealCpuMonitor") from e

    def getTemperature(self) -> float:
        """Get current CPU temperature in Celsius.

        Returns:
            CPU temperature in Celsius, formatted to 2 decimal places
        """
        temp = self._cpu.temperature
        return round(temp, 2)
