import logging
import time
from Event import Event


class Watchdog:
    """Safety watchdog that monitors critical system conditions.

    Enforces safety rules and responds to violations:
    - Heater-pump interlock: Heater must never run without pump
    - Network connectivity: Stops heater if network connection lost
    - MQTT connectivity: Stops heater if remote control unavailable
    - Extended MQTT outage: Full system shutdown after 5 minutes

    The watchdog operates on a priority system:
    1. CRITICAL: Heater-pump interlock (immediate hardStop)
    2. HIGH: Network/MQTT loss (stop heater, allow pump for circulation)
    3. SEVERE: Extended MQTT outage (full system shutdown)

    Attributes:
        pump: Pump controller reference
        heater: Heater controller reference
        light: Light controller reference
        lightColorLogic: Light color logic reference
        pinger: Network connectivity monitor
        messageBus: MQTT message bus reference
        config: Configuration singleton
    """

    def __init__(self, config, pinger, pump, heater, light, lightColorLogic, messageBus):
        """Initialize watchdog with system component references.

        Args:
            config: Configuration singleton
            pinger: Network connectivity monitor
            pump: Pump controller
            heater: Heater controller
            light: Light controller
            lightColorLogic: Light color logic
            messageBus: MQTT message bus
        """
        self.pump = pump
        self.heater = heater
        self.light = light
        self.lightColorLogic = lightColorLogic
        self.pinger = pinger
        self.config = config
        self.messageBus = messageBus

    def check(self):
        """Check safety conditions and respond to violations.

        PRIORITY: Stop heater FIRST, then handle other devices.
        """
        # CRITICAL: Heater-pump interlock check
        if self.heater.isOn() and not self.pump.isOn():
            logging.critical("Watchdog: SAFETY VIOLATION - heater on without pump!")
            # Stop heater IMMEDIATELY - this is the dangerous condition
            self.heater.hardStop()
            Event.logOpaqueEvent("watchdog_heater_emergency_stop",
                                {"reason": "pump_not_running"})
            # Note: We do NOT stop pump here - it's already off

        # Non-blocking connectivity checks
        self._checkConnectivityNonBlocking()
        self._checkMessageBusConnectivity()

    def _checkConnectivityNonBlocking(self):
        """Check network connectivity without blocking safety checks."""
        if self.pinger.isConnected() is False:
            logging.warning("Watchdog: Network connectivity lost to " +
                           self.config.pingTarget)
            # Only stop heater - pump circulation is safe and beneficial
            self.heater.hardStop()
            Event.logOpaqueEvent("watchdog_network_loss", None)
            # Note: Light and pump continue - not safety critical

    def _checkMessageBusConnectivity(self):
        """Handle MQTT disconnection with fail-safe behavior."""
        if not self.messageBus.isConnected():
            # Track disconnection duration
            if not hasattr(self, '_mqtt_disconnect_time'):
                self._mqtt_disconnect_time = time.time()
                logging.warning("Watchdog: MQTT disconnection detected")

            # Attempt reconnection
            self.messageBus.connect()

            # SAFETY: If heater is on and MQTT down, stop heating
            # (allows pump to continue for circulation)
            if self.heater.isOn():
                logging.warning("Watchdog: Stopping heater due to MQTT loss - no remote control")
                self.heater.hardStop()
                Event.logOpaqueEvent("watchdog_mqtt_heater_stop", None)

            # Extended outage: escalate response
            disconnect_duration = time.time() - self._mqtt_disconnect_time
            if disconnect_duration > 300:  # 5 minutes
                logging.error(f"Watchdog: MQTT offline for {disconnect_duration:.0f}s - full safety stop")
                self.pump.hardStop()
                self.heater.hardStop()
                Event.logOpaqueEvent("watchdog_mqtt_extended_outage",
                                    {"duration_seconds": disconnect_duration})
        else:
            # Connection restored
            if hasattr(self, '_mqtt_disconnect_time'):
                duration = time.time() - self._mqtt_disconnect_time
                logging.info(f"Watchdog: MQTT reconnected after {duration:.0f}s")
                Event.logOpaqueEvent("watchdog_mqtt_reconnected",
                                    {"outage_duration_seconds": duration})
                del self._mqtt_disconnect_time
