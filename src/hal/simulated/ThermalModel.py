"""
ThermalModel.py - Physics-based thermal calculations for pool simulation
"""

import logging
from .SimulationConfig import SimulationConfig


class ThermalModel:
    """Physics-based thermal model for pool heating simulation.

    This class implements the thermal calculations for:
    - Heater output temperature based on intake temperature and heater state
    - Pool temperature changes over time based on heating/cooling dynamics

    Attributes:
        config: SimulationConfig instance with thermal parameters
    """

    def __init__(self, config: SimulationConfig):
        """Initialize thermal model with configuration.

        Args:
            config: SimulationConfig instance with thermal parameters
        """
        self.config = config
        logging.info("ThermalModel: Initialized with heater_delta=%.1fC, max_output=%.1fC",
                     config.heater_delta, config.max_heater_output_temp)

    def calculateHeaterOutputTemp(self, intakeTemp: float, isHeaterOn: bool, isPumpOn: bool) -> float:
        """Calculate heater output temperature based on intake temp and device states.

        The heater can only heat water when both the heater and pump are ON.
        When heating, the output temperature is the intake temperature plus the
        heater delta, capped at the maximum safe output temperature.

        Args:
            intakeTemp: Temperature of water entering heater (Celsius)
            isHeaterOn: True if heater is ON
            isPumpOn: True if pump is ON

        Returns:
            Heater output temperature (Celsius)
        """
        # Heater only works when both heater and pump are ON
        if not isHeaterOn or not isPumpOn:
            return intakeTemp

        # Calculate heated temperature with safety limit
        heatedTemp = intakeTemp + self.config.heater_delta
        outputTemp = min(heatedTemp, self.config.max_heater_output_temp)

        # Log if we're hitting safety limit
        if heatedTemp > self.config.max_heater_output_temp:
            logging.warning("ThermalModel: Heater output capped at safety limit %.1fC (would be %.1fC)",
                            self.config.max_heater_output_temp, heatedTemp)

        return outputTemp

    def calculatePoolTemperatureChange(self, currentPoolTemp: float, ambientTemp: float,
                                        isHeaterOn: bool, isPumpOn: bool, elapsedSeconds: float) -> float:
        """Calculate change in pool temperature over elapsed time.

        Pool temperature dynamics:
        - When heating (heater ON, pump ON): Pool warms toward heater output at heating_rate
        - When idle (heater OFF or pump OFF) and pool > ambient: Pool cools toward ambient at heat_loss_rate
        - When idle and pool <= ambient: No temperature change

        Args:
            currentPoolTemp: Current pool water temperature (Celsius)
            ambientTemp: Ambient air temperature (Celsius)
            isHeaterOn: True if heater is ON
            isPumpOn: True if pump is ON
            elapsedSeconds: Time elapsed since last update (seconds)

        Returns:
            Change in pool temperature (positive = warming, negative = cooling) (Celsius)
        """
        # Convert elapsed time to hours for rate calculations
        elapsedHours = elapsedSeconds / 3600.0

        # Heating: Both heater and pump must be ON
        if isHeaterOn and isPumpOn:
            # Pool warms at configured heating rate
            tempChange = self.config.pool_heating_rate_per_hour * elapsedHours
            return tempChange

        # Cooling: Pool loses heat to ambient when warmer than ambient
        if currentPoolTemp > ambientTemp:
            # Pool cools at configured heat loss rate
            tempChange = -self.config.pool_heat_loss_rate_per_hour * elapsedHours
            # Don't cool below ambient temperature
            if currentPoolTemp + tempChange < ambientTemp:
                tempChange = ambientTemp - currentPoolTemp
            return tempChange

        # No temperature change when pool is at or below ambient and not heating
        return 0.0
