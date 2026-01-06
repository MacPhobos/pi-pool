"""
SimulationEnvironment.py - Singleton managing simulated pool environment state
"""

import logging
import time
import random
from typing import Optional
from .SimulationConfig import SimulationConfig
from .ThermalModel import ThermalModel
from .IDeviceStateProvider import IDeviceStateProvider


class SimulationEnvironment:
    """Singleton managing the simulated pool environment state.

    This class maintains the current state of the simulated pool environment,
    including water and ambient temperatures. It uses a thermal model to update
    temperatures based on device states and elapsed time.

    The singleton pattern ensures there is only one simulation environment instance,
    matching the singleton pattern used by Config.py.

    Attributes:
        poolTemperature: Current pool water temperature (Celsius)
        ambientTemperature: Current ambient air temperature (Celsius)
        lastUpdateTime: Timestamp of last physics update (seconds since epoch)
        thermalModel: ThermalModel instance for physics calculations
        deviceStateProvider: Provider for querying device states
        config: SimulationConfig instance
    """

    __instance = None

    @staticmethod
    def getInstance():
        """Get the singleton instance of SimulationEnvironment.

        Returns:
            SimulationEnvironment singleton instance

        Raises:
            RuntimeError: If getInstance() called before instance created
        """
        if SimulationEnvironment.__instance is None:
            raise RuntimeError("SimulationEnvironment: getInstance() called before instance created")
        return SimulationEnvironment.__instance

    def __init__(self, config: SimulationConfig):
        """Initialize the simulation environment singleton.

        Args:
            config: SimulationConfig instance with simulation parameters

        Raises:
            RuntimeError: If instance already exists (singleton violation)
        """
        if SimulationEnvironment.__instance is not None:
            raise RuntimeError("SimulationEnvironment: Singleton instance already exists. Use getInstance()")

        self.config = config
        self.thermalModel = ThermalModel(config)
        self.deviceStateProvider: Optional[IDeviceStateProvider] = None

        # Initialize environment state
        self.poolTemperature = config.initial_pool_temperature
        self.ambientTemperature = config.initial_ambient_temperature
        self.lastUpdateTime = time.time()

        SimulationEnvironment.__instance = self

        logging.info("SimulationEnvironment: Initialized - pool=%.1fC, ambient=%.1fC, time_multiplier=%.1fx",
                     self.poolTemperature, self.ambientTemperature, config.time_multiplier)

    def setDeviceStateProvider(self, provider: IDeviceStateProvider) -> None:
        """Set the device state provider for querying device states.

        This should be called after devices (pump, heater, light) are created
        to wire up the simulation to actual device states.

        Args:
            provider: IDeviceStateProvider implementation
        """
        self.deviceStateProvider = provider
        logging.info("SimulationEnvironment: Device state provider connected")

    def tick(self) -> None:
        """Update simulation physics based on elapsed time.

        This should be called once per main loop iteration. It calculates the
        elapsed time since the last update, applies the time multiplier, and
        updates the pool temperature based on thermal dynamics.
        """
        currentTime = time.time()
        elapsedSeconds = currentTime - self.lastUpdateTime
        self.lastUpdateTime = currentTime

        # Apply time multiplier for faster simulation
        simulatedElapsedSeconds = elapsedSeconds * self.config.time_multiplier

        # Skip update if no device state provider connected yet
        if self.deviceStateProvider is None:
            return

        # Get current device states
        isHeaterOn = self.deviceStateProvider.isHeaterOn()
        isPumpOn = self.deviceStateProvider.isPumpOn()

        # Calculate pool temperature change
        tempChange = self.thermalModel.calculatePoolTemperatureChange(
            self.poolTemperature,
            self.ambientTemperature,
            isHeaterOn,
            isPumpOn,
            simulatedElapsedSeconds
        )

        # Update pool temperature
        oldTemp = self.poolTemperature
        self.poolTemperature += tempChange

        # Log significant temperature changes (> 0.1C)
        if abs(tempChange) > 0.1:
            logging.info("SimulationEnvironment: Pool temperature %.2fC -> %.2fC (%.2fC change, heater=%s, pump=%s)",
                         oldTemp, self.poolTemperature, tempChange, isHeaterOn, isPumpOn)

    def getPoolTemperature(self) -> float:
        """Get current pool water temperature with sensor noise.

        Returns:
            Pool temperature with random noise applied (Celsius)
        """
        noise = random.uniform(-self.config.sensor_noise, self.config.sensor_noise)
        return self.poolTemperature + noise

    def getHeaterOutputTemperature(self) -> float:
        """Get current heater output temperature with sensor noise.

        The heater output temperature depends on the pool temperature (intake)
        and whether the heater and pump are running.

        Returns:
            Heater output temperature with random noise applied (Celsius)
        """
        if self.deviceStateProvider is None:
            # Fallback: return pool temperature if no device state provider
            return self.getPoolTemperature()

        isHeaterOn = self.deviceStateProvider.isHeaterOn()
        isPumpOn = self.deviceStateProvider.isPumpOn()

        outputTemp = self.thermalModel.calculateHeaterOutputTemp(
            self.poolTemperature,
            isHeaterOn,
            isPumpOn
        )

        noise = random.uniform(-self.config.sensor_noise, self.config.sensor_noise)
        return outputTemp + noise

    def getAmbientTemperature(self) -> float:
        """Get current ambient air temperature with sensor noise.

        Returns:
            Ambient temperature with random noise applied (Celsius)
        """
        noise = random.uniform(-self.config.sensor_noise, self.config.sensor_noise)
        return self.ambientTemperature + noise

    def setPoolTemperature(self, temp: float) -> None:
        """Set pool temperature (for MQTT control/testing).

        Args:
            temp: New pool temperature (Celsius)
        """
        logging.info("SimulationEnvironment: Pool temperature manually set to %.1fC", temp)
        self.poolTemperature = temp

    def setAmbientTemperature(self, temp: float) -> None:
        """Set ambient temperature (for MQTT control/testing).

        Args:
            temp: New ambient temperature (Celsius)
        """
        logging.info("SimulationEnvironment: Ambient temperature manually set to %.1fC", temp)
        self.ambientTemperature = temp

    def setSimulationSpeed(self, multiplier: float) -> None:
        """Set simulation time multiplier (for MQTT control/testing).

        Args:
            multiplier: Time multiplier (1.0 = real-time, 60.0 = 1 hour per minute)
        """
        logging.info("SimulationEnvironment: Time multiplier set to %.1fx", multiplier)
        self.config.time_multiplier = multiplier
