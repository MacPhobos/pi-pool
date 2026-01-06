import logging
import threading

from DB import DB
from Event import Event
from Timer import Timer
from RelayBlock import RelayBlock
from PumpState import PumpState
from PumpMode import PumpMode


class Pump:
    """Pool pump controller with timer tracking and multiple operational modes.

    Controls pool pump via GPIO relay with support for timed operations and
    thread-safe state management. Tracks runtime for maintenance tracking and
    energy monitoring.

    Attributes:
        state: Current pump state (ON/OFF)
        mode: Operational mode (OFF, REACH_TIME_AND_STOP)
        timer: Runtime tracker for logging duration
        relayBlock: GPIO relay block interface
        relayBlockPort: Port number on relay block (1-8)
    """

    mode = PumpMode.OFF

    def __init__(self, relayBlock: RelayBlock, pumpPort: int):
        """Initialize pump controller.

        Args:
            relayBlock: GPIO relay block for hardware control
            pumpPort: Port number on relay block (1-8)
        """
        self.db = DB.getInstance()
        self.timer = Timer()
        self.relayBlock = relayBlock
        self.relayBlockPort = pumpPort
        self.state = PumpState.OFF
        self.mode = PumpMode.OFF
        self.runForXMinutes = None
        # State lock to prevent race conditions with heater
        # Uses RLock to allow reentrant locking (setModeOff() calls off())
        self._state_lock = threading.RLock()
        self.off()

    def on(self):
        """Turn pump on with thread-safe state management."""
        # Acquire state lock to prevent race conditions
        with self._state_lock:
            logging.info("Pump On - " + self.getState().name + " -> ON")
            if self.getState() == PumpState.ON:
                return

            Event.logStateEvent("pump_state", self.getState().name, "ON")

            self.relayBlock.portOn(self.relayBlockPort)
            self.state = PumpState.ON

            # Only start timer if not in a timed mode
            if self.mode != PumpMode.REACH_TIME_AND_STOP:
                self.startPumpTimer()

    def off(self):
        """Turn pump off with thread-safe state management."""
        # Acquire state lock to prevent race conditions
        with self._state_lock:
            logging.info("Pump Off - " + self.getState().name + " -> OFF")
            if self.getState() == PumpState.OFF:
                return

            Event.logStateEvent("pump_state", self.getState().name, "OFF")

            self.relayBlock.portOff(self.relayBlockPort)
            self.state = PumpState.OFF
            self.setModeOff()
            self.stopPumpTimer()

    def hardStop(self):
        """Emergency stop for pump - immediately turn off.

        Called by watchdog or safety systems when immediate shutdown required.
        Logs hardstop event and delegates to normal off() procedure.
        """
        logging.info("Pump: HARDSTOP")
        Event.logOpaqueEvent("pump_hard_stop", None)
        self.off()

    def getState(self):
        return self.state

    def isOn(self):
        return self.state == PumpState.ON

    def getMode(self):
        return self.mode

    def getMessage(self):
        status = {"pump_state": self.getState().value}
        return status

    def startPumpTimer(self):
        self.timer.start()

    def stopPumpTimer(self):
        startTime, elapsedSeconds = self.timer.stop()
        self.db.logDuration("pump_time", startTime, elapsedSeconds)

    def setStateMessageHandler(self, data):
        if data == PumpState.ON.value:
            self.on()
        if data == PumpState.OFF.value:
            self.off()

    def setOnMessageHandler(self, data):
        if data == PumpState.ON.value:
            self.on()

    def setOffMessageHandler(self, data):
        if data == PumpState.OFF.value:
            self.off()

    def setRunForXMinutesAndStop(self, durationInMinutes):
        logging.info("Pump Mode: " + PumpMode.REACH_TIME_AND_STOP.name + " - " + self.getMode().name + " -> " + PumpMode.REACH_TIME_AND_STOP.name)
        logging.info("Pump Reach and Stop after minutes: " + str(durationInMinutes))
        Event.logOpaqueEvent("pump_run_for_x_minutes", str(durationInMinutes))

        self.stopPumpTimer()
        self.startPumpTimer()
        self.runForXMinutes = durationInMinutes
        self.mode = PumpMode.REACH_TIME_AND_STOP
        self.on()

    def setModeOff(self):
        if self.getMode() != PumpMode.OFF:
            logging.info("Pump Mode: " + PumpMode.OFF.name + " - " + self.getMode().name + " -> " + PumpMode.OFF.name)
            Event.logOpaqueEvent("pump_mode_off", None)

        self.mode = PumpMode.OFF
        self.runForXMinutes = None
        self.off()

    def runOneLoop(self):
        """Execute one iteration of pump control loop.

        Called every ~1 second by main loop. Handles timed pump operations
        and mode transitions. Checks if timer has reached target duration
        for REACH_TIME_AND_STOP mode.
        """

        if self.getState() == PumpState.OFF and self.getMode() != PumpMode.OFF:
            self.setModeOff()
            return

        if self.mode == PumpMode.REACH_TIME_AND_STOP:
            if self.timer.elapsedSeconds() / 60 > self.runForXMinutes:
                self.off()
                return
            logging.info("Pump On Timer - elapsed: " + str(round(self.timer.elapsedSeconds() / 60, 2)) + " min - target is: " + str(self.runForXMinutes) + " min")
