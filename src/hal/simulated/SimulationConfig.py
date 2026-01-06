"""
SimulationConfig.py - Configuration for thermal simulation physics
"""

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Configuration for thermal simulation parameters.

    Attributes:
        initial_pool_temperature: Starting pool water temperature (Celsius)
        initial_ambient_temperature: Starting ambient/air temperature (Celsius)
        heater_delta: Temperature rise through heater when ON (Celsius)
        max_heater_output_temp: Safety limit for heater output (Celsius)
        pool_heating_rate_per_hour: Rate of pool temperature increase when heating (C/hr)
        pool_heat_loss_rate_per_hour: Rate of pool temperature decrease when idle (C/hr)
        time_multiplier: Simulation speed multiplier (60 = 1 hour per minute)
        sensor_noise: Random noise amplitude for sensor readings (Celsius)
    """

    initial_pool_temperature: float = 26.0
    initial_ambient_temperature: float = 22.0
    heater_delta: float = 10.0
    max_heater_output_temp: float = 40.0
    pool_heating_rate_per_hour: float = 5.0
    pool_heat_loss_rate_per_hour: float = 0.5
    time_multiplier: float = 1.0
    sensor_noise: float = 0.05

    @classmethod
    def fromDict(cls, data: dict) -> 'SimulationConfig':
        """Create config from dictionary (config.json section).

        Args:
            data: Dictionary containing configuration values

        Returns:
            SimulationConfig instance with values from dict or defaults
        """
        return cls(
            initial_pool_temperature=data.get('initial_pool_temperature', 26.0),
            initial_ambient_temperature=data.get('initial_ambient_temperature', 22.0),
            heater_delta=data.get('heater_delta', 10.0),
            max_heater_output_temp=data.get('max_heater_output_temp', 40.0),
            pool_heating_rate_per_hour=data.get('pool_heating_rate_per_hour', 5.0),
            pool_heat_loss_rate_per_hour=data.get('pool_heat_loss_rate_per_hour', 0.5),
            time_multiplier=data.get('time_multiplier', 1.0),
            sensor_noise=data.get('sensor_noise', 0.05)
        )
