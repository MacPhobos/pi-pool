# Hardware Abstraction Layer (HAL)

**Status**: Implemented
**Last Updated**: January 2026

---

## Overview

The Hardware Abstraction Layer (HAL) enables PiPool to run on any platform by abstracting hardware dependencies behind interfaces. The system supports two modes:

- **Real Hardware Mode**: Runs on Raspberry Pi with actual GPIO pins, temperature sensors, and peripherals
- **Simulated Mode**: Runs on any platform (macOS, Linux, Windows) with realistic mock hardware

This allows development without Raspberry Pi hardware, enables comprehensive testing, and provides safe failure scenario testing.

### Hardware Dependencies Abstracted

The HAL abstracts the following hardware interactions:

- **GPIO Control** - `RelayBlock.py` wraps `RPi.GPIO` for relay switching (8-channel relay board)
- **1-Wire Temperature Sensors** - `Thermometer.py` reads DS18B20 sensors via `/sys/bus/w1/devices/`
- **CPU Temperature** - `RpiTemperature.py` uses `gpiozero.CPUTemperature`
- **Network Connectivity** - `Pinger.py` uses `pythonping` for connectivity monitoring
- **System Module Loading** - `pipool.py` loads kernel modules via `modprobe` (w1-gpio, w1-therm)

---

## Quick Start

### Development (Simulated Hardware)
```bash
# Run on any platform without hardware
export PIPOOL_HARDWARE_MODE=simulated
uv run python src/pipool.py
```

### Production (Real Hardware)
```bash
# Run on Raspberry Pi with actual hardware
export PIPOOL_HARDWARE_MODE=real
uv run python src/pipool.py
```

### Auto-Detect
```bash
# Automatically detects Raspberry Pi and selects mode
uv run python src/pipool.py
```

---

## Architecture

### Before HAL
```
┌─────────────────────────────────────────┐
│        Application Layer                │
│  Pump, Heater, Light, Sensors           │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│    Direct Hardware Dependencies          │
│  RPi.GPIO, 1-Wire, pythonping            │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│   Raspberry Pi Hardware REQUIRED         │
└──────────────────────────────────────────┘

❌ Cannot develop without Raspberry Pi
❌ Cannot run tests
❌ Cannot test failures safely
```

### With HAL
```
┌─────────────────────────────────────────┐
│        Application Layer                │
│  Pump, Heater, Light, Sensors           │
│        (NO CHANGES REQUIRED)            │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│    Hardware Abstraction Layer           │
│    IGpioController, ITemperatureSensor  │
│    INetworkMonitor, ICpuMonitor         │
└─────┬───────────────────────────┬───────┘
      ↓                           ↓
┌─────────────────┐     ┌─────────────────┐
│ Real Hardware   │     │ Simulated       │
│ (Raspberry Pi)  │     │ (Any Platform)  │
│                 │     │                 │
│ • RPi.GPIO      │     │ • Mock objects  │
│ • 1-Wire FS     │     │ • State logs    │
│ • pythonping    │     │ • Realistic sim │
└─────────────────┘     └─────────────────┘

✅ Run on any platform
✅ Full test coverage
✅ Safe failure testing
```

---

## HAL Interfaces

The HAL defines five core interfaces that abstract all hardware interactions.

### 1. IGpioController
Controls GPIO pins for relay boards (pump, heater, light control).

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from enum import Enum

class PinMode(Enum):
    BCM = "BCM"
    BOARD = "BOARD"

class PinState(Enum):
    HIGH = 1
    LOW = 0

class PinDirection(Enum):
    IN = "IN"
    OUT = "OUT"

class IGpioController(ABC):
    @abstractmethod
    def set_mode(self, mode: PinMode) -> None:
        """Set GPIO pin numbering mode (BCM or BOARD)."""
        pass

    @abstractmethod
    def setup(self, pin: int, direction: PinDirection) -> None:
        """Configure a GPIO pin as input or output."""
        pass

    @abstractmethod
    def output(self, pin: int, state: PinState) -> None:
        """Set the output state of a GPIO pin."""
        pass

    @abstractmethod
    def input(self, pin: int) -> PinState:
        """Read the input state of a GPIO pin."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release GPIO resources."""
        pass
```

### 2. ITemperatureSensor
Reads temperature from 1-Wire DS18B20 sensors.

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Tuple

class ITemperatureSensor(ABC):
    @abstractmethod
    def read_temperature(self) -> Tuple[str, float]:
        """
        Read temperature from sensor.
        Returns: Tuple of (sensor_name, temperature_celsius)
        Raises: SensorReadError if sensor read fails after retries
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the sensor name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if sensor is available/connected."""
        pass
```

### 3. ICpuMonitor
Monitors Raspberry Pi CPU temperature.

**Interface Definition**:
```python
from abc import ABC, abstractmethod

class ICpuMonitor(ABC):
    @abstractmethod
    def get_temperature(self) -> float:
        """
        Get current CPU temperature in Celsius.
        Returns: Temperature as float with 2 decimal precision
        """
        pass
```

### 4. INetworkMonitor
Checks network connectivity via ping.

**Interface Definition**:
```python
from abc import ABC, abstractmethod

class INetworkMonitor(ABC):
    @abstractmethod
    def ping(self, target: str, count: int = 10, interval: int = 1) -> bool:
        """
        Ping a target host to check connectivity.
        Returns: True if at least one ping succeeded, False otherwise
        """
        pass
```

### 5. ISystemLoader
Loads kernel modules (e.g., w1-gpio, w1-therm).

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import List

class ISystemLoader(ABC):
    @abstractmethod
    def load_modules(self, modules: List[str]) -> None:
        """
        Load kernel modules.
        Raises: SystemLoadError if module loading fails
        """
        pass
```

---

## Configuration

### Mode Selection Priority

1. **Environment Variable** (highest priority):
   ```bash
   export PIPOOL_HARDWARE_MODE=simulated
   ```

2. **Config File** (config.json or config_custom.json):
   ```json
   {
     "hardwareMode": "real"
   }
   ```

3. **Auto-Detect** (lowest priority):
   - Checks `/proc/cpuinfo` for "Raspberry Pi"
   - If found: uses `real` mode
   - Otherwise: uses `simulated` mode

### Legacy Support
The `NO_DEVICES=1` environment variable is still supported and maps to simulated mode.

### Configuration File Examples

#### Real Hardware Config (config.json)
```json
{
    "hardwareMode": "real",
    "tempSensors": {
        "in_to_heater": {
            "name": "temp_sensor_in",
            "device": "/sys/bus/w1/devices/28-3c01d607777b"
        },
        "out_from_heater": {
            "name": "temp_sensor_out",
            "device": "/sys/bus/w1/devices/28-3c55f649ce7e"
        },
        "temp_ambient": {
            "name": "temp_ambient",
            "device": "/sys/bus/w1/devices/28-3c01d607831d"
        }
    },
    "pumpPort": 8,
    "heaterPort": 7,
    "lightPort": 6,
    "maxWaterTemp": 33,
    "pingTarget": "192.168.1.23"
}
```

#### Simulated Hardware Config (config.sim.json)
```json
{
    "hardwareMode": "simulated",
    "tempSensors": {
        "in_to_heater": {
            "name": "temp_sensor_in",
            "device": "/simulated/temp_in"
        },
        "out_from_heater": {
            "name": "temp_sensor_out",
            "device": "/simulated/temp_out"
        },
        "temp_ambient": {
            "name": "temp_ambient",
            "device": "/simulated/temp_ambient"
        }
    },
    "pumpPort": 8,
    "heaterPort": 7,
    "lightPort": 6,
    "maxWaterTemp": 33,
    "pingTarget": "8.8.8.8",
    "simulationSettings": {
        "heaterWattsPerSecond": 100,
        "waterVolumeLiters": 20000,
        "ambientCoolingRate": 0.5
    }
}
```

---

## File Structure

```
src/
├── hal/
│   ├── __init__.py              # HardwareFactory
│   ├── interfaces.py            # All HAL interfaces
│   ├── simulated/
│   │   ├── SimulatedGpioController.py
│   │   ├── SimulatedTemperatureSensor.py
│   │   ├── SimulatedCpuMonitor.py
│   │   ├── SimulatedNetworkMonitor.py
│   │   └── SimulatedSystemLoader.py
│   └── real/
│       ├── RealGpioController.py
│       ├── RealTemperatureSensor.py
│       ├── RealCpuMonitor.py
│       ├── RealNetworkMonitor.py
│       └── RealSystemLoader.py
├── Config.py                    # Hardware mode detection
├── RelayBlock.py                # Accepts IGpioController
├── Thermometer.py               # Accepts ITemperatureSensor
├── RpiTemperature.py            # Accepts ICpuMonitor
├── Pinger.py                    # Accepts INetworkMonitor
└── pipool.py                    # Creates HardwareFactory
```

---

## Usage Examples

### How Components Use HAL

Application components use HAL interfaces through dependency injection:

```python
# RelayBlock uses GPIO interface
class RelayBlock:
    def __init__(self, gpio_controller: IGpioController):
        self.gpio = gpio_controller
        self.gpio.set_mode(PinMode.BCM)
        # Initialize pins...

    def pinOn(self, gpioPin):
        self.gpio.output(gpioPin, PinState.LOW)  # Relay ON = LOW

    def pinOff(self, gpioPin):
        self.gpio.output(gpioPin, PinState.HIGH)  # Relay OFF = HIGH
```

```python
# Thermometer uses Temperature interface
class Thermometer:
    def __init__(self, config, sensor: ITemperatureSensor):
        self.sensor = sensor
        self.name = config["name"]
        name, temp_c = self.sensor.read_temperature()
        self.setCurrentTemp(temp_c)

    def readTemp(self):
        name, temp_c = self.sensor.read_temperature()
        self.setCurrentTemp(temp_c)
        return name, temp_c
```

```python
# RpiTemperature uses CPU monitor interface
class RpiTemperature:
    def __init__(self, cpu_monitor: ICpuMonitor):
        self.cpu_monitor = cpu_monitor

    def getCurrentTemp(self):
        return self.cpu_monitor.get_temperature()
```

---

## Dependency Injection Flow

```
Start pipool.py
     ↓
Load Config → Read hardwareMode from env/config/auto-detect
     ↓
Create HardwareFactory(mode)
     ↓
Create HAL implementations:
  gpio = factory.createGpioController()
  temp_in = factory.createTemperatureSensor(...)
  temp_out = factory.createTemperatureSensor(...)
  cpu = factory.createCpuMonitor()
  network = factory.createNetworkMonitor()
     ↓
Inject into application classes:
  relayBlock = RelayBlock(gpio)
  thermometer_in = Thermometer(config, temp_in)
  rpiTemp = RpiTemperature(cpu)
  pinger = Pinger(config, network)
     ↓
Run application (code unchanged!)
```

---

## Testing with HAL

### Unit Tests
Test individual components with mocked HAL interfaces:

```python
# Test pump logic without hardware
def test_pump_state_transition():
    mock_gpio = Mock(IGpioController)
    relay_block = RelayBlock(mock_gpio)
    pump = Pump(relay_block)

    pump.setState(PumpState.ON)
    mock_gpio.output.assert_called_with(PUMP_PIN, GPIO.LOW)
```

### Integration Tests
Test with simulated hardware:

```python
# Test heater automation with simulated hardware
def test_heater_reaches_target():
    config = Config()
    factory = HardwareFactory("simulated")

    gpio = factory.createGpioController()
    temp_sensor = factory.createTemperatureSensor("/tmp", "pool")

    relay_block = RelayBlock(gpio)
    heater = Heater(relay_block, temp_sensor)

    heater.setTargetTemperature(28.0)
    # Verify heater turns on when below target
```

### Test Components
```bash
# Verify HAL components load correctly
export PIPOOL_HARDWARE_MODE=simulated
python -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from hal import HardwareFactory

config = Config()
factory = HardwareFactory(config.getHardwareMode())

gpio = factory.createGpioController()
sensor = factory.createTemperatureSensor('/tmp', 'test')
cpu = factory.createCpuMonitor()
net = factory.createNetworkMonitor()

print('All HAL components created successfully!')
"
```

---

## Simulated Hardware Behavior

### Simulated GPIO
- Maintains in-memory pin state dictionary
- Logs all pin state changes
- No actual GPIO hardware access

### Simulated Temperature Sensor
- Returns realistic temperatures (25-30°C)
- Drift simulation (+0.05°C/min) to model temperature changes over time
- Sensor noise (±0.2°C) to simulate real sensor behavior
- Manual override available: `set_temperature(temp)` for testing scenarios

### Simulated Network Monitor
- Always returns `True` (connected) by default
- Manual override available: `set_connection_state(connected)` for testing network failures

### Simulated CPU Monitor
- Returns realistic CPU temperature (40-50°C)
- Slight random variance to simulate real CPU behavior

---

## Advanced Simulation Features

### Temperature Physics Simulation

Simulated sensors can model realistic water temperature dynamics:

```python
class WaterTemperatureSimulator:
    """Models water temperature dynamics with heating and cooling."""

    def update(self, heater_on: bool, pump_on: bool, elapsed_seconds: float):
        # Heat added by heater (if on and pump running)
        if heater_on and pump_on:
            energy_joules = self.heater_watts * elapsed_seconds
            temp_increase = energy_joules / (self.water_mass_kg * self.specific_heat)
            self.current_temp += temp_increase

        # Natural cooling to ambient (Newton's law of cooling)
        temp_diff = self.current_temp - self.ambient_temp
        cooling_rate = self.cooling_coefficient * temp_diff * elapsed_seconds
        self.current_temp -= cooling_rate
```

This enables realistic simulation of:
- Water heating when heater is on
- Natural cooling to ambient temperature
- Pump dependency (no heating without pump)

### Manual Override for Testing

Simulated components support manual overrides for scenario testing:

```python
# Override temperature for testing
simulated_sensor.set_temperature(35.0)  # Test overheating scenario

# Override network connectivity for testing
simulated_network.set_connection_state(False)  # Test network failure
```

### Scenario Testing

Test complex scenarios safely in simulation mode:

- **Heater reaches target**: Verify heater turns off at target temperature
- **Network loss**: Test watchdog safety shutdown on connectivity loss
- **Sensor failure**: Verify heater stops when temperature sensor fails
- **Overheating**: Test emergency shutdown if water exceeds max temperature

---

## Benefits

### Development
- ✅ Develop on laptop without Raspberry Pi
- ✅ Faster iteration (no deploy cycle)
- ✅ IDE debugging with breakpoints

### Testing
- ✅ Unit tests without hardware
- ✅ Test dangerous scenarios safely (heater overheating, sensor failures)
- ✅ CI/CD pipeline support
- ✅ Repeatable test scenarios

### Safety
- ✅ Test failures without equipment damage
- ✅ Test watchdog safety shutdowns
- ✅ Test network loss scenarios

### Operations
- ✅ Training environment for operators
- ✅ Self-documenting simulation mode
- ✅ Production behavior unchanged (100% backwards compatible)

---

## Future Possibilities

### Record & Replay Mode
Record real hardware sessions and replay in simulation for debugging:
```bash
# Record 1 hour of real operation
python pipool.py --mode real --record session_001.json

# Replay recorded session in simulation
python pipool.py --mode simulated --replay session_001.json
```

### Hybrid Mode
Mix real and simulated hardware for partial testing:
```json
{
    "hardwareMode": "hybrid",
    "gpioController": "simulated",
    "temperatureSensors": "real",
    "networkMonitor": "simulated"
}
```

### Remote Hardware
Control real hardware over network for remote development:
```json
{
    "hardwareMode": "remote",
    "remoteHost": "raspberrypi.local",
    "remotePort": 8080
}
```

### Hardware-in-the-Loop (HIL) Testing
Run some components on real hardware, others simulated:
- Sensors: Real (actual data)
- Actuators: Simulated (safety - no physical control)
- Database: Real
- Network: Real

---

## Challenges & Mitigations

### Simulation Fidelity
**Challenge**: Simulated hardware may not match real behavior exactly

**Mitigations**:
- Use real hardware to calibrate simulation parameters
- Log real sensor data and replay in simulation
- Keep simulation conservative (shorter timeouts, etc.)
- Test on real hardware before production deployment

### Maintaining Two Implementations
**Challenge**: Keep real and simulated HAL in sync

**Mitigations**:
- Comprehensive interface contracts with clear specifications
- Shared test suite that runs against both implementations
- Automated tests that verify both real and simulated modes
- Interface changes require updates to both implementations

### Database in Simulation
**Challenge**: Should simulation use real PostgreSQL or mock database?

**Options**:
1. **Separate schema**: Use `pipool_sim` database for simulation data
2. **SQLite**: Use SQLite for simulation (requires DB abstraction)
3. **Mock DB**: Log database operations to files instead of DB

**Current Approach**: Use separate database schema for simulation mode

---

## Troubleshooting

### Application won't start in real mode
**Problem**: `ImportError: No module named 'RPi.GPIO'`
**Solution**: Install RPi.GPIO on Raspberry Pi: `pip install RPi.GPIO`

### Simulated mode not activating
**Problem**: Running on laptop but still trying to use real GPIO
**Solution**: Explicitly set mode: `export PIPOOL_HARDWARE_MODE=simulated`

### Auto-detect not working
**Problem**: Running on Raspberry Pi but using simulated mode
**Solution**: Check `/proc/cpuinfo` contains "Raspberry Pi", or explicitly set mode to `real`

### Legacy NO_DEVICES flag
**Problem**: `NO_DEVICES=1` not working
**Solution**: This is mapped to simulated mode. Use `PIPOOL_HARDWARE_MODE=simulated` instead (preferred).

---

## Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `PIPOOL_HARDWARE_MODE` | `simulated`, `real` | Override hardware mode detection |
| `NO_DEVICES` | `1` | Legacy flag (maps to simulated mode) |

---

## See Also

- [CLAUDE.md](../CLAUDE.md) - Project coding standards
- [README.md](../README.md) - General project overview
- [schema.sql](../schema.sql) - Database schema
