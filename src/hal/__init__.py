"""Hardware abstraction layer for PiPool.

This package provides a hardware abstraction layer (HAL) that enables running
the PiPool system on real Raspberry Pi hardware or in simulation mode on any platform.

Main components:
- HardwareFactory: Factory for creating hardware implementations
- HardwareMode: Enum for selecting real or simulated mode
- Interfaces: Abstract base classes for all hardware components
- Real implementations: Wrappers around actual hardware libraries
- Simulated implementations: Software simulations for testing

Usage:
    from hal import HardwareFactory, HardwareMode

    factory = HardwareFactory(HardwareMode.SIMULATED)
    gpio = factory.createGpioController()
    sensor = factory.createTemperatureSensor("/dev/null", "temp_sensor_in")
"""
from .HardwareFactory import HardwareFactory, HardwareMode
from .interfaces import (
    IGpioController,
    PinMode,
    PinState,
    PinDirection,
    ITemperatureSensor,
    ICpuMonitor,
    INetworkMonitor,
    ISystemLoader,
)

__all__ = [
    'HardwareFactory',
    'HardwareMode',
    'IGpioController',
    'PinMode',
    'PinState',
    'PinDirection',
    'ITemperatureSensor',
    'ICpuMonitor',
    'INetworkMonitor',
    'ISystemLoader',
]
