"""Real temperature sensor using 1-Wire filesystem."""
import logging
import time
from typing import Tuple
from hal.interfaces import ITemperatureSensor


class RealTemperatureSensor(ITemperatureSensor):
    """Real hardware temperature sensor implementation reading from 1-Wire filesystem."""

    def __init__(self, devicePath: str, sensorName: str):
        """Initialize the real temperature sensor.

        Args:
            devicePath: Path to 1-Wire device (e.g., /sys/bus/w1/devices/28-XXXX/w1_slave)
            sensorName: Human-readable sensor name
        """
        self.devicePath = devicePath
        self.sensorName = sensorName
        self.maxRetries = 10
        logging.info(f"RealTemperatureSensor: Initialized '{sensorName}' at {devicePath}")

    def readTemperature(self) -> Tuple[str, float]:
        """Read temperature from 1-Wire sensor with retry logic.

        Returns:
            Tuple of (sensor_name, temperature_celsius)

        Raises:
            RuntimeError: If temperature cannot be read after max retries
        """
        for attempt in range(self.maxRetries):
            try:
                with open(self.devicePath, 'r') as f:
                    lines = f.readlines()

                # Verify CRC check passed
                if len(lines) < 2 or 'YES' not in lines[0]:
                    if attempt < self.maxRetries - 1:
                        time.sleep(0.2)
                        continue
                    raise RuntimeError(f"CRC check failed for {self.sensorName}")

                # Parse temperature from second line
                temp_pos = lines[1].find('t=')
                if temp_pos == -1:
                    raise RuntimeError(f"Temperature data not found for {self.sensorName}")

                temp_string = lines[1][temp_pos + 2:]
                temp_c = float(temp_string) / 1000.0

                # Format to 2 decimal places
                temp_c = round(temp_c, 2)

                return (self.sensorName, temp_c)

            except (IOError, OSError) as e:
                if attempt < self.maxRetries - 1:
                    logging.warning(f"RealTemperatureSensor: Read attempt {attempt + 1} failed for {self.sensorName}: {e}")
                    time.sleep(0.2)
                    continue
                else:
                    logging.error(f"RealTemperatureSensor: Failed to read {self.sensorName} after {self.maxRetries} attempts: {e}")
                    raise RuntimeError(f"Cannot read temperature from {self.sensorName}") from e

        raise RuntimeError(f"Failed to read temperature from {self.sensorName} after {self.maxRetries} attempts")

    def getName(self) -> str:
        """Get the sensor name."""
        return self.sensorName

    def isAvailable(self) -> bool:
        """Check if sensor is available by attempting to read the device file."""
        try:
            with open(self.devicePath, 'r') as f:
                f.read()
            return True
        except (IOError, OSError):
            return False
