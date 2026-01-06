import logging
import time
import threading
from Timer import Timer

from DB import DB
from Event import Event
from RelayBlock import RelayBlock
from HeaterState import HeaterState
from HeaterMode import HeaterMode

"""
REMOTE CONTROL CONNECTION: Remote control can be
accomplished via a 2-wire or 3-wire connection (see
Figure22b). The 2-wire connection allows thermostat control
where the remote temperature is sensed and calls for heat
when needed. The 3- wire remote switches function between
“POOL” and “SPA”. The set point temperatures for “POOL”
and “SPA” operation are still controlled locally. The 3-wire
remote simply provides a convenient way to manage the
“POOL” or “SPA” mode selection. Remote wiring is
accomplished using the factory supplied remote wire harness.
Remote wiring must be run in a separate conduit from power
supply. Use 22 AWG wire for runs less than 30 feet. Use 20
AWG wire for runs over 30 feet. The maximum allowable run is
200 feet.

2-WIRE REMOTE CONTROL CONNECTION: Connect the
appropriate wires from the remote control to the factory
harness ORANGE wire (“POOL”) and WHITE wire (“COM”). To
configure the heater for 2-wire remote thermostat control, use
the “MODE” key on the heater keypad to put the control into
“STANDBY” mode. Then simultaneously press and hold the “(
- )” and “MODE” keys for 3 seconds until the display shows the
code “bo” (bypass operation). Once in bypass operation, press
the ‘MODE’ button until ‘POOL’ or ‘SPA’ LED is illuminated.
The control is now ready to operate in 2-wire remote
thermostat control. The heater’s thermostat will only function
to limit the return water temperature to a maximum of 104°F. 
"""


class Heater:
    """Pool heater controller with comprehensive safety interlocks.

    Controls pool heater via GPIO relay with mandatory safety checks:
    - Requires pump running (heater cannot operate without water flow)
    - Maximum water temperature limit (prevents overheating)
    - Maximum runtime limit (prevents runaway heating)
    - Sensor staleness detection (stops if temperature readings stale)
    - Thread-safe activation with dual-locking to prevent race conditions

    Safety is paramount - heater operations use atomic pump verification
    with dual locking to ensure pump cannot stop between verification
    and heater activation.

    Attributes:
        state: Current heater state (ON/OFF)
        mode: Operational mode (OFF, HOLD, REACH_AND_STOP)
        targetTemp: Target temperature for heating modes
        inputTemp: Current water temperature entering heater
        outputTemp: Current water temperature exiting heater
        pump: Reference to pump for safety interlock
        maxWaterTemp: Maximum allowed water temperature
        maxRuntimeSeconds: Maximum continuous runtime limit
    """

    state = HeaterState.OFF
    mode = HeaterMode.OFF
    targetTemp = 0
    inputTemp = 0
    outputTemp = 0

    def __init__(self, relayBlock: RelayBlock, heaterPort: int, maxWaterTemp: int, pump=None, maxRuntimeSeconds=None):
        """Initialize Heater with safety limits.

        Args:
            relayBlock: Relay block for GPIO control
            heaterPort: Port number on relay block
            maxWaterTemp: Maximum water temperature limit (safety)
            pump: Pump reference for safety interlock
            maxRuntimeSeconds: Maximum continuous runtime in seconds
                              Default: 4 hours (14400 seconds) from config or fallback
        """
        self.timer = Timer()
        self.db = DB.getInstance()
        self.relayBlock = relayBlock
        self.relayBlockPort = heaterPort
        self.maxWaterTemp = maxWaterTemp
        self.pump = pump  # Reference to pump for safety checks
        self.lastInputTempUpdate = 0  # Track when sensor was last updated
        self._activation_lock = threading.Lock()  # Prevent race condition with pump

        # Maximum runtime to prevent runaway heating
        if maxRuntimeSeconds is not None:
            self.maxRuntimeSeconds = maxRuntimeSeconds
        else:
            # Try to get from config, fallback to 4 hours
            try:
                from Config import Config
                self.maxRuntimeSeconds = Config.getInstance().maxHeaterRuntimeSeconds
            except (AttributeError, KeyError) as e:
                logging.warning(f"Heater: Could not read maxHeaterRuntimeSeconds from config: {e}. Using default 4 hours")
                self.maxRuntimeSeconds = 4 * 3600  # 4 hours default

        self.hardStop()

    def hardStop(self):
        """Emergency stop for heater - immediately turn off.

        Called by watchdog or safety systems when immediate shutdown required.
        Resets mode to OFF and stops heater operation. This is the highest
        priority safety mechanism for the heater.
        """
        # Event.logOpaqueEvent("heater_hard_stop", None)
        self.setModeOff()
        self.off()

    def on(self):
        """Turn on heater with atomic pump verification.

        Uses dual locking to prevent race condition where pump could stop
        between checking pump state and activating heater GPIO. The heater's
        activation lock and pump's state lock are both held during the
        critical section, ensuring atomic verification and activation.

        Returns:
            bool: True if heater successfully activated, False otherwise
        """
        # Atomic pump verification with dual locking
        with self._activation_lock:
            # If we have a pump reference, acquire its state lock to prevent
            # pump state changes during heater activation
            if self.pump is not None:
                # Acquire pump's state lock to prevent pump from turning off
                # while we verify and activate heater
                with self.pump._state_lock:
                    # Verify pump is running (pump cannot change state while we hold lock)
                    if not self.pump.isOn():
                        logging.error("Heater: Cannot turn on - pump is not running")
                        Event.logOpaqueEvent("heater_blocked_no_pump", {})
                        return False

                    if self.getState() != HeaterState.OFF:
                        logging.info("Heater On - " + self.getState().name + " -> ON")
                        Event.logStateEvent("heater_state", self.getState().name, HeaterState.ON.name)

                    # ATOMIC: Pump cannot change state until we release both locks
                    # Activate heater GPIO while holding pump lock
                    self.relayBlock.portOn(self.relayBlockPort)
                    self.state = HeaterState.ON
                    self.timer.start()
                    logging.info("Heater: Activated with atomic pump verification")
                    return True
            else:
                # No pump reference - allow heater to turn on (backward compatibility)
                if self.getState() != HeaterState.OFF:
                    logging.info("Heater On - " + self.getState().name + " -> ON")
                    Event.logStateEvent("heater_state", self.getState().name, HeaterState.ON.name)

                self.relayBlock.portOn(self.relayBlockPort)
                self.state = HeaterState.ON
                self.timer.start()
                logging.warning("Heater: Activated without pump reference (no safety interlock)")
                return True

    def off(self):
        """Turn off heater and log runtime.

        Stops heater operation, resets mode to OFF, stops timer, and logs
        duration to database. Safe to call when already off (idempotent).
        """
        if self.getState() != HeaterState.OFF:
            logging.info("Heater Off - " + self.getState().name + " -> OFF")
            Event.logStateEvent("heater_state", self.getState().name, HeaterState.OFF.name)

        self.relayBlock.portOff(self.relayBlockPort)
        self.state = HeaterState.OFF
        self.setModeOff()
        startTime, elapsedSeconds = self.timer.stop()
        self.db.logDuration("heater_time", startTime, elapsedSeconds)

    def isOn(self):
        return self.state == HeaterState.ON

    def getState(self):
        return self.state

    def getMode(self):
        return self.mode

    def getMessage(self):
        status = { "heater_state": self.getState().value }
        return status

    def setInputTemp(self, inputTemp):
        # Validate sensor data for safety
        if inputTemp is None or inputTemp <= 0:
            logging.error("Heater: Invalid input temperature, stopping for safety")
            self.hardStop()
            return
        self.inputTemp = inputTemp
        self.lastInputTempUpdate = time.time()

    def setOutputTemp(self, outputTemp):
        self.outputTemp = outputTemp

    def setModeHoldTemp(self, temp):
        logging.info("Heater Mode: " + HeaterMode.HOLD.name + " - " + self.getMode().name + " -> " + HeaterMode.HOLD.name)
        logging.info("Heater Hold Temp: " + str(temp))
        Event.logOpaqueEvent("heater_mode_hold_temp", str(temp))

        self.targetTemp = temp
        self.mode = HeaterMode.HOLD

    def setModeReachTempAndStop(self, temp):
        logging.info("Heater Mode: " + HeaterMode.REACH_AND_STOP.name + " - " + self.getMode().name + " -> " + HeaterMode.REACH_AND_STOP.name)
        logging.info("Heater Reach and Stop Temp: " + str(temp))
        Event.logOpaqueEvent("heater_mode_reach_and_stop", str(temp))

        self.targetTemp = temp
        self.mode = HeaterMode.REACH_AND_STOP

    def setModeOff(self):
        if self.getMode() != HeaterMode.OFF:
            logging.info("Heater Mode: " + HeaterMode.OFF.name + " - " + self.getMode().name + " -> " + HeaterMode.OFF.name)
            Event.logOpaqueEvent("heater_mode_off", None)

        self.mode = HeaterMode.OFF

    def inputTempLessThen(self, targetTemp: int):
        return self.inputTemp < targetTemp

    def runOneLoop(self):
        """Execute one iteration of heater control loop.

        Called every ~1 second by main loop. Performs critical safety checks:
        - Verifies pump still running if heater is on
        - Checks maximum runtime limit hasn't been exceeded
        - Validates temperature sensor data is fresh
        - Enforces maximum temperature limit
        - Manages HOLD and REACH_AND_STOP modes

        All safety violations result in immediate hardStop().
        """
        # Verify pump still running every loop when heater is on
        if self.state == HeaterState.ON:
            if self.pump is not None and not self.pump.isOn():
                logging.error("Heater: EMERGENCY - Pump stopped while heater running!")
                self.hardStop()
                Event.logOpaqueEvent("heater_emergency_pump_stopped", None)
                return

            # Check maximum runtime to prevent runaway heating
            runtime = self.timer.elapsedSeconds()
            if runtime > self.maxRuntimeSeconds:
                hours = self.maxRuntimeSeconds / 3600
                logging.error(f"Heater: SAFETY LIMIT - Maximum runtime of {hours:.1f} hours exceeded!")
                self.hardStop()
                Event.logOpaqueEvent("heater_max_runtime_exceeded", {
                    "runtime_seconds": runtime,
                    "limit_seconds": self.maxRuntimeSeconds
                })
                return

        # Check sensor staleness
        if self.lastInputTempUpdate > 0:
            sensor_age_seconds = time.time() - self.lastInputTempUpdate
            if sensor_age_seconds > 60:  # No reading in 60 seconds
                logging.error(f"Heater: Input sensor stale ({sensor_age_seconds}s old), stopping for safety")
                self.hardStop()
                return

        if self.state == HeaterState.OFF:
            self.off()
            return

        if self.inputTemp >= self.maxWaterTemp:
            self.off()
            return

        if self.mode == HeaterMode.REACH_AND_STOP:
            if self.inputTempLessThen(self.targetTemp) is True:
                logging.info("Heater: Heating from " + str(self.inputTemp) + " to " + str(self.targetTemp))
                self.on()
                return

            if self.inputTempLessThen(self.targetTemp) is False:
                logging.info("Heater: Target temp " + str(self.targetTemp) + " reached. Stopping.")
                Event.logOpaqueEvent("heater_mode_reach_and_stop", "reached " + str(self.targetTemp))
                self.off()
                self.mode = HeaterMode.OFF
                return

        if self.mode == HeaterMode.HOLD:
            if self.inputTemp < self.targetTemp:
                logging.info("Heater: ON holding at " + str(self.targetTemp) + " waterTemp: " + str(self.inputTemp))
                self.on()
                return
            else:
                logging.info("Heater: OFF - target temp of " + str(self.targetTemp) + " reached.")
                self.off()
                return

    def setStateMessageHandler(self, data):
        if data == HeaterState.ON.value:
            self.on()
        if data == HeaterState.OFF.value:
            self.off()


