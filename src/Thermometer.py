import time
import json
import logging


class Thermometer:

    currentTemp = 0

    def __init__(self, config, temperatureSensor=None):
        from hal.interfaces import ITemperatureSensor

        logging.info("Thermometer() config: " + json.dumps(config))
        self.name = config["name"]
        self.device = config["device"]

        # Use injected sensor or create one
        if temperatureSensor is None:
            # Backward compatibility: create sensor based on hardware mode
            from Config import Config
            from hal import HardwareFactory
            cfg = Config.getInstance()
            factory = HardwareFactory(cfg.getHardwareMode())
            self.sensor = factory.createTemperatureSensor(self.device, self.name)
        else:
            self.sensor = temperatureSensor

        name, temp_c = self.readTemp()
        self.setCurrentTemp(temp_c)

    def getName(self):
        return self.name

    def setCurrentTemp(self, temp):
        self.currentTemp = temp

    def getCurrentTemp(self):
        return self.currentTemp

    def getCurrentReading(self):
        return self.getCurrentTemp()

    def readTemp(self):
        """Read temperature from sensor.

        Returns None instead of stale data on read error. This allows callers
        to detect sensor failures and respond appropriately (e.g., safety
        shutdown) rather than operating on outdated data.

        Returns:
            tuple: (sensor_name, temperature) on success
            tuple: (sensor_name, None) on read error - caller must handle!
        """
        try:
            name, temp_c = self.sensor.readTemperature()
            self.setCurrentTemp(temp_c)
            return name, temp_c
        except Exception as e:
            logging.error(f"Sensor {self.name} read error: {e}")
            # Return None instead of stale data - callers must handle None appropriately
            return self.name, None
    
    def status(self):
        name, temp_c = self.readTemp()
        status = {name: temp_c}
        return status
