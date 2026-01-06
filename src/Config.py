import json
import logging
import os
from os.path import exists

class Config:
    """Singleton configuration loader for PiPool system.

    Loads configuration from JSON files with support for custom overrides:
    - config.json: Default configuration (committed to repo)
    - config_custom.json: Local overrides (gitignored, takes precedence)

    Configuration includes:
    - Hardware: GPIO ports, relay assignments, sensor addresses
    - Safety: Maximum temperatures, runtime limits
    - Network: MQTT broker, ping target
    - Database: PostgreSQL connection parameters
    - Hardware mode: Real or simulated hardware

    The singleton pattern ensures consistent configuration across all components.
    """

    __instance = None

    def __init__(self):
        """Initialize config singleton.

        Raises:
            Exception: If singleton already initialized
        """
        if Config.__instance is not None:
            raise Exception("Singleton already initialized")
        else:
            Config.__instance = self
            self.readConfig()

    @staticmethod
    def getInstance():
        """Get singleton instance of Config.

        Returns:
            Config: The singleton configuration instance

        Raises:
            Exception: If Config not yet instantiated
        """
        if Config.__instance is None:
            raise Exception("Instantiate first")
        return Config.__instance

    def readConfig(self):
        """Load configuration from JSON file with validation.

        Loads config_custom.json if present, otherwise config.json.
        Reads all configuration parameters including:
        - Temperature sensor addresses
        - GPIO relay port assignments
        - Safety limits (max temperature, max heater runtime)
        - Network settings (MQTT broker, ping target)
        - Database credentials

        Performs validation checks on configuration values for safety.

        Raises:
            ValueError: If required configuration missing or invalid
        """

        self.noDevices = os.getenv('NO_DEVICES')
        if self.noDevices is not None:
            self.noDevices = True

        if exists("config_custom.json"):
            configFileName = "config_custom.json"
        else:
            configFileName = "config.json"

        logging.info("Loading config: " + configFileName)

        with open(configFileName, "r") as jsonfile:
            data = json.load(jsonfile)

        self.tempSensorIn = data["tempSensors"]["in_to_heater"]
        self.tempSensorOut = data["tempSensors"]["out_from_heater"]
        self.tempAmbient = data["tempSensors"]["temp_ambient"]
        self.pumpPort = data["pumpPort"]
        self.lightPort = data["lightPort"]
        self.heaterPort = data["heaterPort"]

        self.pumpSpeedS1Port = data["pumpSpeedS1Port"]
        self.pumpSpeedS2Port = data["pumpSpeedS2Port"]
        self.pumpSpeedS3Port = data["pumpSpeedS3Port"]
        self.pumpSpeedS4Port = data["pumpSpeedS4Port"]

        self.maxWaterTemp = data["maxWaterTemp"]

        # Maximum heater runtime to prevent runaway heating
        # Default: 4 hours (4 * 3600 = 14400 seconds)
        self.maxHeaterRuntimeSeconds = data.get("maxHeaterRuntimeSeconds", 4 * 3600)

        self.pingTarget = data["pingTarget"]

        # MQTT broker address (must be provided in config.json)
        if "mqttBroker" not in data:
            raise ValueError("mqttBroker must be specified in config.json - no default fallback available")
        self.mqttBroker = data["mqttBroker"]

        self.dbName = data["dbName"]
        self.dbUser = data["dbUser"]
        self.dbPassword = data["dbPassword"]

        # Read simulation configuration
        if "simulation" in data:
            self.simulationConfig = data["simulation"]
        else:
            self.simulationConfig = {}

        # Read hardware mode
        env_mode = os.getenv('PIPOOL_HARDWARE_MODE')
        if env_mode:
            self.hardwareMode = env_mode
        elif "hardwareMode" in data:
            self.hardwareMode = data["hardwareMode"]
        else:
            # Auto-detect: check if running on Raspberry Pi
            self.hardwareMode = self._detectHardwareMode()

        logging.info(f"Hardware mode: {self.hardwareMode}")

        # HIGH-1 Fix: Validate configuration
        self._validateConfig()

    def _validateConfig(self):
        """Validate configuration values for correctness and safety"""

        # Validate sensor paths exist (only if not in NO_DEVICES mode)
        if not self.noDevices:
            for sensor_key, sensor_config in [
                ("in_to_heater", self.tempSensorIn),
                ("out_from_heater", self.tempSensorOut),
                ("temp_ambient", self.tempAmbient)
            ]:
                device_path = sensor_config["device"]
                if not exists(device_path):
                    logging.warning(f"Sensor {sensor_key} path does not exist: {device_path}")

        # Validate GPIO ports are in valid range
        valid_ports = [1, 2, 3, 4, 5, 6, 7, 8]
        port_configs = [
            ("pumpPort", self.pumpPort),
            ("lightPort", self.lightPort),
            ("heaterPort", self.heaterPort),
            ("pumpSpeedS1Port", self.pumpSpeedS1Port),
            ("pumpSpeedS2Port", self.pumpSpeedS2Port),
            ("pumpSpeedS3Port", self.pumpSpeedS3Port),
            ("pumpSpeedS4Port", self.pumpSpeedS4Port)
        ]

        for port_name, port_value in port_configs:
            if port_value not in valid_ports:
                raise ValueError(f"Invalid {port_name}: {port_value} (must be 1-8)")

        # Validate temperature is reasonable
        if self.maxWaterTemp < 20 or self.maxWaterTemp > 45:
            logging.warning(f"maxWaterTemp {self.maxWaterTemp}°C seems unusual (recommended: 20-45°C)")

        # Validate ping target is not empty
        if not self.pingTarget or self.pingTarget.strip() == "":
            logging.warning("pingTarget is empty - network monitoring may not work")

        logging.info("Configuration validation complete")

    def _detectHardwareMode(self) -> str:
        """Auto-detect if running on Raspberry Pi."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    return 'real'
        except (IOError, OSError) as e:
            logging.debug(f"Hardware detection: Could not read /proc/cpuinfo: {e}")
        return 'simulated'

    def getHardwareMode(self):
        """Get the hardware mode as HardwareMode enum."""
        from hal import HardwareMode
        if self.hardwareMode == 'real':
            return HardwareMode.REAL
        else:
            return HardwareMode.SIMULATED
