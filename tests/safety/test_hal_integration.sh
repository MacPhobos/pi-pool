#!/bin/bash
# HAL Phase 2 Integration Test Script
# Tests all modified components in simulated mode

set -e  # Exit on error

echo "======================================================================"
echo "HAL Phase 2 Integration Test"
echo "======================================================================"
echo ""

# Set environment for simulated mode
export PIPOOL_HARDWARE_MODE=simulated
export NO_DEVICES=1

echo "Environment:"
echo "  PIPOOL_HARDWARE_MODE=$PIPOOL_HARDWARE_MODE"
echo "  NO_DEVICES=$NO_DEVICES"
echo ""

# Test 1: Basic component imports
echo "Test 1: Testing component imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from hal import HardwareFactory
from RelayBlock import RelayBlock
from Thermometer import Thermometer
from RpiTemperature import RpiTemperature
from Pinger import Pinger
print('✓ All imports successful')
"
echo ""

# Test 2: Config and factory
echo "Test 2: Testing Config and HardwareFactory..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from hal import HardwareFactory

config = Config()
print(f'✓ Hardware mode: {config.hardwareMode}')

factory = HardwareFactory(config.getHardwareMode())
print('✓ HardwareFactory created')
"
echo ""

# Test 3: All HAL components
echo "Test 3: Testing HAL component creation..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from hal import HardwareFactory

config = Config()
factory = HardwareFactory(config.getHardwareMode())

gpio = factory.createGpioController()
print('✓ GPIO controller')

sensor = factory.createTemperatureSensor('/tmp', 'test')
print('✓ Temperature sensor')

cpu = factory.createCpuMonitor()
print('✓ CPU monitor')

net = factory.createNetworkMonitor()
print('✓ Network monitor')

sys_loader = factory.createSystemLoader()
print('✓ System loader')
"
echo ""

# Test 4: Application components with DI
echo "Test 4: Testing application components with DI..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from hal import HardwareFactory
from RelayBlock import RelayBlock
from Thermometer import Thermometer
from RpiTemperature import RpiTemperature

config = Config()
factory = HardwareFactory(config.getHardwareMode())

gpio = factory.createGpioController()
relay = RelayBlock(gpio)
print('✓ RelayBlock with DI')

sensor = factory.createTemperatureSensor('/tmp', 'test')
thermo = Thermometer({'name': 'test', 'device': '/tmp'}, sensor)
print(f'✓ Thermometer with DI: {thermo.getCurrentTemp()}°C')

cpu = factory.createCpuMonitor()
rpi = RpiTemperature(cpu)
print(f'✓ RpiTemperature with DI: {rpi.getCurrentTemp()}°C')
"
echo ""

# Test 5: Backward compatibility
echo "Test 5: Testing backward compatibility (no DI)..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from Config import Config
from RelayBlock import RelayBlock
from Thermometer import Thermometer
from RpiTemperature import RpiTemperature

config = Config()

relay = RelayBlock()
print('✓ RelayBlock without DI')

thermo = Thermometer({'name': 'test', 'device': '/tmp'})
print(f'✓ Thermometer without DI: {thermo.getCurrentTemp()}°C')

rpi = RpiTemperature()
print(f'✓ RpiTemperature without DI: {rpi.getCurrentTemp()}°C')
"
echo ""

echo "======================================================================"
echo "✅ All HAL integration tests passed!"
echo "======================================================================"
