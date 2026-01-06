# Hardware Abstraction Layer (HAL)

## Overview

The HAL enables the PiPool system to run on real Raspberry Pi hardware OR in simulation mode on any platform. This is essential for development, testing, and CI/CD without requiring physical hardware.

## Architecture

```
hal/
├── __init__.py                    # Package exports
├── HardwareFactory.py             # Factory for creating implementations
├── interfaces/                    # Abstract interfaces
│   ├── IGpioController.py         # GPIO control interface
│   ├── ITemperatureSensor.py      # Temperature sensor interface
│   ├── ICpuMonitor.py             # CPU temperature interface
│   ├── INetworkMonitor.py         # Network connectivity interface
│   └── ISystemLoader.py           # Kernel module loader interface
├── real/                          # Real hardware implementations
│   ├── RealGpioController.py      # RPi.GPIO wrapper
│   ├── RealTemperatureSensor.py   # 1-Wire sensor reader
│   ├── RealCpuMonitor.py          # gpiozero CPU temp wrapper
│   ├── RealNetworkMonitor.py      # pythonping wrapper
│   └── RealSystemLoader.py        # modprobe wrapper
└── simulated/                     # Simulated implementations
    ├── SimulatedGpioController.py # In-memory GPIO simulation
    ├── SimulatedTemperatureSensor.py # Temperature simulation
    ├── SimulatedCpuMonitor.py     # CPU temp simulation
    ├── SimulatedNetworkMonitor.py # Network simulation
    └── SimulatedSystemLoader.py   # Module loader simulation
```

## Usage

### Basic Usage

```python
from hal import HardwareFactory, HardwareMode

# Create factory (mode can be REAL or SIMULATED)
factory = HardwareFactory(HardwareMode.SIMULATED)

# Create hardware components
gpio = factory.createGpioController()
temp_sensor = factory.createTemperatureSensor("/dev/w1/...", "temp_sensor_in")
cpu_monitor = factory.createCpuMonitor()
network_monitor = factory.createNetworkMonitor()
system_loader = factory.createSystemLoader()
```

### GPIO Control

```python
from hal.interfaces import PinMode, PinDirection, PinState

# Setup GPIO
gpio.setMode(PinMode.BCM)
gpio.setup(17, PinDirection.OUT)

# Control pin
gpio.output(17, PinState.HIGH)
gpio.output(17, PinState.LOW)

# Read pin
state = gpio.input(17)  # Returns PinState.HIGH or PinState.LOW

# Cleanup
gpio.cleanup()
```

### Temperature Sensors

```python
# Read temperature
name, temp = temp_sensor.readTemperature()  # Returns ("temp_sensor_in", 26.42)

# Check availability
if temp_sensor.isAvailable():
    name, temp = temp_sensor.readTemperature()
```

### CPU Monitor

```python
# Get CPU temperature
cpu_temp = cpu_monitor.getTemperature()  # Returns float (e.g., 52.3)
```

### Network Monitor

```python
# Ping a host
is_connected = network_monitor.ping("8.8.8.8", count=10, interval=1)
```

### System Loader

```python
# Load kernel modules
system_loader.loadModules(['w1-gpio', 'w1-therm'])
```

## Hardware Modes

### REAL Mode

Uses actual Raspberry Pi hardware:
- Requires `RPi.GPIO` library
- Requires `gpiozero` library
- Requires `pythonping` library
- Reads from 1-Wire filesystem
- Performs actual GPIO operations
- Loads actual kernel modules

### SIMULATED Mode

Software simulation for testing:
- No hardware dependencies
- Runs on any platform (Linux, macOS, Windows)
- Simulates realistic behavior:
  - GPIO state tracking
  - Temperature readings with variance
  - CPU temperature 40-60°C
  - Network always connected (configurable)
- Logs all operations for debugging

## Simulated Hardware Details

### GPIO Simulation
- Tracks pin states in memory
- Validates pin directions before operations
- Logs all setup/output/input operations

### Temperature Simulation
- Base temperatures per sensor:
  - `temp_sensor_in`: 26.0°C
  - `temp_sensor_out`: 27.0°C
  - `temp_ambient`: 22.0°C
- Random variance: ±0.2°C
- Slow drift: 0.1°C per hour

### CPU Simulation
- Base temperature: 50.0°C
- Variance: ±5.0°C
- Range: 40-60°C

### Network Simulation
- Default: Always connected
- Configurable via `setConnectionState(bool)`

## Testing

```bash
# Run in simulated mode
cd /export/workspace/pi-pool/src
python -c "from hal import HardwareFactory, HardwareMode; f = HardwareFactory(HardwareMode.SIMULATED); print('Success')"

# Test all components
python << 'EOF'
from hal import HardwareFactory, HardwareMode
from hal.interfaces import PinMode, PinDirection, PinState

factory = HardwareFactory(HardwareMode.SIMULATED)

# Test GPIO
gpio = factory.createGpioController()
gpio.setMode(PinMode.BCM)
gpio.setup(17, PinDirection.OUT)
gpio.output(17, PinState.HIGH)
print(f"GPIO test passed: {gpio.input(17) == PinState.HIGH}")

# Test temperature sensor
temp = factory.createTemperatureSensor("/dev/null", "test_sensor")
name, value = temp.readTemperature()
print(f"Temperature test passed: {name} = {value:.2f}°C")

# Test CPU monitor
cpu = factory.createCpuMonitor()
print(f"CPU test passed: {cpu.getTemperature():.2f}°C")

# Test network
net = factory.createNetworkMonitor()
print(f"Network test passed: {net.ping('8.8.8.8')}")

# Test system loader
loader = factory.createSystemLoader()
loader.loadModules(['w1-gpio', 'w1-therm'])
print("System loader test passed")
EOF
```

## Error Handling

### Real Mode Errors
- Import errors if libraries missing → RuntimeError
- GPIO errors propagate from RPi.GPIO
- Sensor read failures → RuntimeError after 10 retries
- Network ping failures → Returns False

### Simulated Mode Errors
- No import dependencies
- Validates pin directions (raises ValueError)
- Always succeeds for sensor reads
- Network ping respects connection state

## Future Enhancements

Potential additions for Phase 2+:
- `IDatabase` interface for PostgreSQL abstraction
- `IMqttClient` interface for MQTT abstraction
- `IRelay` interface for relay block abstraction
- Configuration-driven sensor setup
- Hardware failure simulation
- Performance metrics collection
