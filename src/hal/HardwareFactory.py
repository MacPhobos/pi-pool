"""Hardware abstraction layer factory."""
import logging
from enum import Enum
from hal.interfaces import (
    IGpioController,
    ITemperatureSensor,
    ICpuMonitor,
    INetworkMonitor,
    ISystemLoader
)


class HardwareMode(Enum):
    """Hardware abstraction mode."""
    REAL = "real"
    SIMULATED = "simulated"


class HardwareFactory:
    """Factory to create hardware abstraction layer implementations.

    Based on the hardware mode, creates either real or simulated implementations
    of hardware interfaces. This allows the system to run on real Raspberry Pi
    hardware or in simulation mode on any platform.
    """

    def __init__(self, mode: HardwareMode):
        """Initialize the hardware factory.

        Args:
            mode: Hardware mode (REAL or SIMULATED)
        """
        self.mode = mode
        logging.info(f"HardwareFactory: Initializing in {mode.value} mode")

    def createGpioController(self) -> IGpioController:
        """Create a GPIO controller implementation.

        Returns:
            IGpioController implementation based on hardware mode
        """
        if self.mode == HardwareMode.REAL:
            from hal.real import RealGpioController
            return RealGpioController()
        else:
            from hal.simulated import SimulatedGpioController
            return SimulatedGpioController()

    def createTemperatureSensor(self, devicePath: str, sensorName: str) -> ITemperatureSensor:
        """Create a temperature sensor implementation.

        Args:
            devicePath: Path to 1-Wire device (used only in REAL mode)
            sensorName: Human-readable sensor name

        Returns:
            ITemperatureSensor implementation based on hardware mode

        Note:
            In simulated mode, different sensors get different base temperatures:
            - temp_sensor_in: 26.0°C
            - temp_sensor_out: 27.0°C
            - temp_ambient: 22.0°C
        """
        if self.mode == HardwareMode.REAL:
            from hal.real import RealTemperatureSensor
            return RealTemperatureSensor(devicePath, sensorName)
        else:
            from hal.simulated import SimulatedTemperatureSensor

            # Assign different base temperatures for different sensors
            baseTemp = 25.0  # default
            if 'in' in sensorName.lower():
                baseTemp = 26.0
            elif 'out' in sensorName.lower():
                baseTemp = 27.0
            elif 'ambient' in sensorName.lower():
                baseTemp = 22.0

            return SimulatedTemperatureSensor(sensorName, baseTemperature=baseTemp)

    def createCpuMonitor(self) -> ICpuMonitor:
        """Create a CPU monitor implementation.

        Returns:
            ICpuMonitor implementation based on hardware mode
        """
        if self.mode == HardwareMode.REAL:
            from hal.real import RealCpuMonitor
            return RealCpuMonitor()
        else:
            from hal.simulated import SimulatedCpuMonitor
            return SimulatedCpuMonitor()

    def createNetworkMonitor(self) -> INetworkMonitor:
        """Create a network monitor implementation.

        Returns:
            INetworkMonitor implementation based on hardware mode
        """
        if self.mode == HardwareMode.REAL:
            from hal.real import RealNetworkMonitor
            return RealNetworkMonitor()
        else:
            from hal.simulated import SimulatedNetworkMonitor
            return SimulatedNetworkMonitor()

    def createSystemLoader(self) -> ISystemLoader:
        """Create a system loader implementation.

        Returns:
            ISystemLoader implementation based on hardware mode
        """
        if self.mode == HardwareMode.REAL:
            from hal.real import RealSystemLoader
            return RealSystemLoader()
        else:
            from hal.simulated import SimulatedSystemLoader
            return SimulatedSystemLoader()
