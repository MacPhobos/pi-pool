"""Simulated temperature sensor for testing without hardware."""
import logging
import random
from typing import Tuple
from hal.interfaces import ITemperatureSensor


class SimulatedTemperatureSensor(ITemperatureSensor):
    """Simulated temperature sensor implementation using physics-based simulation.

    This sensor queries the SimulationEnvironment singleton to get realistic
    temperature readings that respond to heater and pump state changes.

    Sensor type is auto-detected from the sensor name:
    - 'in' or 'intake': Pool intake temperature
    - 'out' or 'output': Heater output temperature
    - 'ambient': Ambient air temperature
    - Default: Pool temperature
    """

    def __init__(self, sensorName: str, baseTemperature: float = 25.0, variance: float = 0.2):
        """Initialize the simulated temperature sensor.

        Args:
            sensorName: Human-readable sensor name (used for type detection)
            baseTemperature: Fallback temperature if SimulationEnvironment not available (Celsius)
            variance: Random variance range (deprecated, kept for compatibility)
        """
        self.sensorName = sensorName
        self.baseTemperature = baseTemperature
        self.variance = variance
        self.currentTemperature = baseTemperature

        # Auto-detect sensor type from name
        nameLower = sensorName.lower()
        if 'in' in nameLower and 'out' not in nameLower:
            self.sensorType = 'intake'
        elif 'out' in nameLower:
            self.sensorType = 'output'
        elif 'ambient' in nameLower:
            self.sensorType = 'ambient'
        else:
            self.sensorType = 'pool'  # Default to pool temperature

        logging.info(f"SimulatedTemperatureSensor: Initialized '{sensorName}' as type '{self.sensorType}'")

    def readTemperature(self) -> Tuple[str, float]:
        """Read simulated temperature from SimulationEnvironment.

        Queries SimulationEnvironment for physics-based temperature readings.
        Falls back to base temperature if SimulationEnvironment not initialized.

        Returns:
            Tuple of (sensor_name, temperature_celsius)
        """
        try:
            # Try to get temperature from SimulationEnvironment
            from .SimulationEnvironment import SimulationEnvironment
            simEnv = SimulationEnvironment.getInstance()

            if self.sensorType == 'intake' or self.sensorType == 'pool':
                temp = simEnv.getPoolTemperature()
            elif self.sensorType == 'output':
                temp = simEnv.getHeaterOutputTemperature()
            elif self.sensorType == 'ambient':
                temp = simEnv.getAmbientTemperature()
            else:
                temp = simEnv.getPoolTemperature()

        except (RuntimeError, ImportError):
            # SimulationEnvironment not initialized yet - use fallback
            temp = self.baseTemperature + random.uniform(-self.variance, self.variance)

        # Format to 2 decimal places
        temp = round(temp, 2)

        self.currentTemperature = temp
        return (self.sensorName, temp)

    def getName(self) -> str:
        """Get the sensor name."""
        return self.sensorName

    def isAvailable(self) -> bool:
        """Check if sensor is available (always True for simulation)."""
        return True

    def setBaseTemperature(self, temperature: float) -> None:
        """Set the base temperature for simulation (helper for testing).

        Args:
            temperature: New base temperature in Celsius
        """
        self.baseTemperature = temperature
        logging.info(f"SimulatedTemperatureSensor: Set base temperature for '{self.sensorName}' to {temperature:.2f}°C")
