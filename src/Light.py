import time
import logging
import threading

from RelayBlock import RelayBlock
from LightState import LightState


class Light:

    def __init__(self, relayBlock: RelayBlock, lightPort: int):
        self.relayBlock = relayBlock
        self.relayBlockPort = lightPort
        self.state = LightState.OFF
        self.lastOnTime = None
        self.lastOffTime = None
        self._cycle_thread = None  # Track background cycle thread
        self._cycle_lock = threading.Lock()  # Prevent concurrent cycles
        self.off()

    def on(self):
        logging.info("Light On")
        self.lastOnTime = time.time()
        self.relayBlock.portOn(self.relayBlockPort)
        self.state = LightState.ON

    def off(self):
        logging.info("Light Off")
        self.lastOffTime = time.time()
        self.relayBlock.portOff(self.relayBlockPort)
        self.state = LightState.OFF

    def isOn(self):
        return self.state == LightState.ON

    def secondsInOffState(self):
        if self.lastOffTime is not None:
            if self.getState() == LightState.ON:
                return 0
            return time.time() - self.lastOffTime
        else:
            return None

    def getState(self):
        return self.state

    def getMessage(self):
        status = { "light_state": self.getState().value }
        return status

    def cycleOne(self, delay=1):
        """Cycle light off then on with delay.

        WARNING: This method blocks for 'delay' seconds.
        Should only be called from background thread.
        """
        self.off()
        time.sleep(delay)
        self.on()

    def _cycle_sync(self, count, delay):
        """Internal synchronous cycle - runs in background thread."""
        with self._cycle_lock:
            for _ in range(count):
                self.cycleOne(delay)
            logging.info(f"Light: Completed {count} cycles")

    def cycle(self, count, delay=1):
        """Cycle light on/off multiple times.

        This method runs asynchronously in a background thread to prevent
        blocking the main control loop. The main loop must remain responsive
        for safety-critical operations (heater, pump, watchdog).

        Args:
            count: Number of on/off cycles to perform
            delay: Seconds between each toggle (default: 1)

        Note:
            - Cycles run asynchronously - method returns immediately
            - Concurrent cycle requests are serialized by _cycle_lock
            - Use isCycling() to check if a cycle operation is in progress
        """
        if count <= 0:
            return

        # Check if called from main thread and warn
        if threading.current_thread() is threading.main_thread():
            logging.warning("Light.cycle() called from main thread - running in background to avoid blocking")

        # Check if already cycling
        if self._cycle_thread is not None and self._cycle_thread.is_alive():
            logging.warning("Light: Cycle already in progress, queuing new cycle")

        # Run cycle in background thread to avoid blocking main loop
        self._cycle_thread = threading.Thread(
            target=self._cycle_sync,
            args=(count, delay),
            name="LightCycleThread"
        )
        self._cycle_thread.daemon = True  # Don't prevent application exit
        self._cycle_thread.start()

        logging.info(f"Light: Started {count} cycles in background (delay={delay}s)")

    def isCycling(self):
        """Check if a cycle operation is currently in progress.

        Returns:
            bool: True if cycling, False otherwise
        """
        return self._cycle_thread is not None and self._cycle_thread.is_alive()

    def waitForCycle(self, timeout=None):
        """Wait for current cycle operation to complete.

        Args:
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            bool: True if cycle completed, False if timeout
        """
        if self._cycle_thread is not None and self._cycle_thread.is_alive():
            self._cycle_thread.join(timeout=timeout)
            return not self._cycle_thread.is_alive()
        return True

    def setStateMessageHandler(self, data):
        if data == LightState.ON.value:
            self.on()
        if data == LightState.OFF.value:
            self.off()
