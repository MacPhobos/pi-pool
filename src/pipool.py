import os
import sys
import time
import json
import logging
import signal
import atexit

from Automations import Automations
from Config import Config
from LightColorLogic import LightColorLogic
from Pinger import Pinger
from RelayBlock import RelayBlock
from Pump import Pump
from Light import Light
from Heater import Heater
from Thermometer import Thermometer
from Sensor import Sensor
from Sensors import Sensors
from MessageBus import MessageBus
from Watchdog import Watchdog
from RpiTemperature import RpiTemperature
from DB import DB
from Event import Event

# Version information
__version__ = "0.1.0"

logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.DEBUG,
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

logging.info(f"PiPool v{__version__} starting")

# Constant variable definition
MQTT_STATUS_TOPIC = "pipool/status"
MQTT_SENSORS_TOPIC = "pipool/sensors"

# Global shutdown flag
_shutdown_requested = False

config = Config()

# Create hardware factory based on mode
from hal import HardwareFactory, HardwareMode
from hal.interfaces import PinMode

hardwareFactory = HardwareFactory(config.getHardwareMode())

# Initialize simulation environment if in simulated mode
if config.getHardwareMode() == HardwareMode.SIMULATED:
    from hal.simulated import SimulationEnvironment, SimulationConfig
    simConfig = SimulationConfig.fromDict(config.simulationConfig.get("thermal", {}))
    simConfig.time_multiplier = config.simulationConfig.get("time_multiplier", 1.0)
    SimulationEnvironment(simConfig)  # Initialize singleton
    logging.info("SimulationEnvironment: Initialized for thermal physics")

# Load kernel modules (no-op in simulation mode)
systemLoader = hardwareFactory.createSystemLoader()
systemLoader.loadModules(['w1-gpio', 'w1-therm'])

db = DB(config)
event = Event(db)

Event.logOpaqueEvent("Boot", None)

# Create HAL components
gpioController = hardwareFactory.createGpioController()

# Temperature sensors using HAL
sensorIn = hardwareFactory.createTemperatureSensor(
    config.tempSensorIn["device"],
    config.tempSensorIn["name"]
)
sensorOut = hardwareFactory.createTemperatureSensor(
    config.tempSensorOut["device"],
    config.tempSensorOut["name"]
)
sensorAmbient = hardwareFactory.createTemperatureSensor(
    config.tempAmbient["device"],
    config.tempAmbient["name"]
)

cpuMonitor = hardwareFactory.createCpuMonitor()
networkMonitor = hardwareFactory.createNetworkMonitor()

# Create application components with HAL dependencies
intakeTempThermo = Thermometer(config.tempSensorIn, sensorIn)
outputTempThermo = Thermometer(config.tempSensorOut, sensorOut)
tempAmbientThermo = Thermometer(config.tempAmbient, sensorAmbient)
rpiTemp = RpiTemperature(cpuMonitor)

sensors = Sensors()
sensors.addSensor(Sensor(intakeTempThermo))
sensors.addSensor(Sensor(outputTempThermo))
sensors.addSensor(Sensor(tempAmbientThermo))
sensors.addSensor(Sensor(rpiTemp))

# RelayBlock with GPIO controller
relayBlock = RelayBlock(gpioController)

pump = Pump(relayBlock, config.pumpPort)
light = Light(relayBlock, config.lightPort)
heater = Heater(relayBlock, config.heaterPort, config.maxWaterTemp, pump)  # Pass pump reference
lightColorLogic = LightColorLogic(light)

# Wire up device state provider for simulation
if config.getHardwareMode() == HardwareMode.SIMULATED:
    from hal.simulated import DeviceStateAdapter, SimulationEnvironment
    deviceStateProvider = DeviceStateAdapter(pump=pump, heater=heater, light=light)
    SimulationEnvironment.getInstance().setDeviceStateProvider(deviceStateProvider)
    logging.info("SimulationEnvironment: Device state provider connected")

automations = Automations(pump, heater, light, lightColorLogic)

# Pinger with network monitor
pinger = Pinger(config, networkMonitor)

messageBus = MessageBus(pump, light, heater, lightColorLogic)
messageBus.addHandler("pipool/control/pump_state",      pump.setStateMessageHandler)
messageBus.addHandler("pipool/control/pump_on",         pump.setOnMessageHandler)
messageBus.addHandler("pipool/control/pump_off",        pump.setOffMessageHandler)

messageBus.addHandler("pipool/control/light_state",     light.setStateMessageHandler)
messageBus.addHandler("pipool/control/light_set_color", lightColorLogic.setColorMessageHandler)
messageBus.addHandler("pipool/control/heater_state",    heater.setStateMessageHandler)
# messageBus.addHandler("pipool/control/heater_mode",     heater.setModeMessageHandler)
messageBus.addHandler("pipool/control/heater_reach_and_stop",  automations.setHeaterReachAndStopMessageHandler)
messageBus.addHandler("pipool/control/pump_run_for_x_minutes", automations.setPumpRunForXMinutesMessageHandler)

# Simulation MQTT handlers (only in simulated mode)
if config.getHardwareMode() == HardwareMode.SIMULATED:
    from hal.simulated import SimulationEnvironment
    simEnv = SimulationEnvironment.getInstance()
    messageBus.addHandler("pipool/simulation/set_pool_temp",
                          lambda data: simEnv.setPoolTemperature(float(data)))
    messageBus.addHandler("pipool/simulation/set_ambient_temp",
                          lambda data: simEnv.setAmbientTemperature(float(data)))
    messageBus.addHandler("pipool/simulation/set_time_multiplier",
                          lambda data: simEnv.setSimulationSpeed(float(data)))
    logging.info("SimulationEnvironment: MQTT handlers registered")

messageBus.connect()
messageBus.addSubscriptions()

watchdog = Watchdog(config, pinger, pump, heater, light, lightColorLogic, messageBus)

def create_shutdown_handler(pump, heater, light, lightColorLogic, pinger, messageBus, gpioController):
    """Factory to create shutdown handler with access to devices.

    Implements ordered shutdown sequence for safety:
    1. Stop heater (highest priority - prevent dry-firing)
    2. Stop pump (safe after heater is off)
    3. Stop non-critical devices (lights)
    4. Stop background services (pinger, MQTT)
    5. Cleanup GPIO (prevent stuck relays)
    """
    def shutdown_handler(signum=None, frame=None):
        global _shutdown_requested

        # Handle second signal - force immediate exit
        if _shutdown_requested:
            logging.warning("Shutdown: Second signal received, forcing exit")
            sys.exit(1)

        _shutdown_requested = True
        signal_name = signal.Signals(signum).name if signum else "MANUAL"
        logging.info(f"Shutdown: Initiated by {signal_name}")

        # Phase 1: Stop heater (CRITICAL - highest priority)
        try:
            heater.hardStop()
            logging.info("Shutdown: Heater stopped")
        except Exception as e:
            logging.error(f"Shutdown: Error stopping heater: {e}", exc_info=True)

        # Phase 2: Stop pump (safe to stop after heater)
        try:
            pump.hardStop()
            logging.info("Shutdown: Pump stopped")
        except Exception as e:
            logging.error(f"Shutdown: Error stopping pump: {e}", exc_info=True)

        # Phase 3: Stop non-critical devices
        try:
            light.off()
            lightColorLogic.stop()
            logging.info("Shutdown: Lights stopped")
        except Exception as e:
            logging.error(f"Shutdown: Error stopping lights: {e}", exc_info=True)

        # Phase 4: Stop background services
        try:
            pinger.stop()
            messageBus.stop()
            logging.info("Shutdown: Background services stopped")
        except Exception as e:
            logging.error(f"Shutdown: Error stopping services: {e}", exc_info=True)

        # Phase 5: GPIO cleanup (CRITICAL - prevents stuck relays)
        try:
            gpioController.cleanup()
            logging.info("Shutdown: GPIO cleanup complete")
        except Exception as e:
            logging.error(f"Shutdown: Error during GPIO cleanup: {e}", exc_info=True)

        logging.info("Shutdown: Complete - exiting")
        Event.logOpaqueEvent("system_shutdown", {"signal": signal_name})
        sys.exit(0)

    return shutdown_handler

# Create and register shutdown handler
shutdown_handler = create_shutdown_handler(
    pump, heater, light, lightColorLogic, pinger, messageBus, gpioController
)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # systemd stop / kill
atexit.register(lambda: shutdown_handler(None, None))  # Normal exit

logging.info("Shutdown: Signal handlers registered (SIGINT, SIGTERM, atexit)")

while not _shutdown_requested:
    try:
        # Update simulation physics
        if config.getHardwareMode() == HardwareMode.SIMULATED:
            from hal.simulated import SimulationEnvironment
            SimulationEnvironment.getInstance().tick()

        messageBus.start()

        message = sensors.collectSensorStatus()
        message.update(pump.getMessage())
        message.update(light.getMessage())
        message.update(heater.getMessage())

        heater.setInputTemp(sensors.getSensor("temp_sensor_in").getCurrentReading())
        heater.setOutputTemp(sensors.getSensor("temp_sensor_out").getCurrentReading())
        heater.runOneLoop()
        pump.runOneLoop()

        watchdog.check()

        logging.info ("Message: " + json.dumps(message))

        messageBus.publish(MQTT_STATUS_TOPIC, 'Online')
        messageBus.publish(MQTT_SENSORS_TOPIC, json.dumps(message))

        messageBus.stop()

        sensors.logSensorsToDb()

        time.sleep(1)

    except Exception as e:
        logging.error(f"Main loop error: {e}", exc_info=True)
        # Implement safe state fallback
        try:
            pump.hardStop()
            heater.hardStop()
            lightColorLogic.hardStop()
            logging.error("Emergency stop triggered due to main loop exception")
        except Exception as stop_error:
            logging.error(f"Error during emergency stop: {stop_error}")
        time.sleep(5)  # Longer delay before retry
