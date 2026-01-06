import json
import logging
from threading import Timer
from Event import Event

# Configuration constant for pump circulation delay
PUMP_CIRCULATION_DELAY_SECONDS = 5  # Time for water to circulate before heater start


class Automations:

    def __init__(self, pump, heater, light, colorLogicLight):
        self.pump = pump
        self.heater = heater
        self.light = light
        self.colorLogicLight = colorLogicLight

    def setHeaterReachAndStopMessageHandler(self, data):
        """Handle heater reach-and-stop command with safety delays.

        Uses non-blocking Timer callback to avoid blocking MQTT thread.
        Adds 5-second pump circulation delay before heater activation
        to prevent dry-firing damage.
        """
        # Validate JSON payload
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as e:
            logging.error(f"Automations: Invalid JSON in heater command: {e}")
            return

        logging.info(f"setReachAndStopMessageHandler payload: {json.dumps(payload)}")

        # Validate mode field
        mode = payload.get('mode')
        if mode is None:
            logging.error("Automations: Missing 'mode' in heater command")
            return

        logging.info(f"setReachAndStopMessageHandler mode: {mode}")

        if mode == "ON":
            # Validate target temperature
            try:
                targetTemp = int(payload.get('targetTemp', 0))
            except (ValueError, TypeError):
                logging.error(f"Automations: Invalid targetTemp: {payload.get('targetTemp')}")
                return

            if targetTemp <= 0 or targetTemp > 45:  # Reasonable pool temp limits
                logging.error(f"Automations: targetTemp {targetTemp} out of range (1-45°C)")
                return

            if self.heater.inputTempLessThen(targetTemp):
                # Step 1: Start pump immediately
                logging.info(f"Automations: Starting pump for heating to {targetTemp}°C")
                self.pump.on()

                # Step 2: Schedule heater start after circulation delay (non-blocking)
                logging.info(f"Automations: Scheduling heater start in {PUMP_CIRCULATION_DELAY_SECONDS}s")
                Timer(
                    PUMP_CIRCULATION_DELAY_SECONDS,
                    self._startHeaterAfterDelay,
                    args=(targetTemp,)
                ).start()
            else:
                logging.info(f"Automations: Current temp already >= {targetTemp}°C, not starting heater")

        elif mode == "OFF":
            logging.info("Automations: Stopping heater via automation")
            self.heater.off()
        else:
            logging.error(f"Automations: Invalid mode '{mode}', expected 'ON' or 'OFF'")

    def _startHeaterAfterDelay(self, targetTemp):
        """Start heater after pump circulation delay.

        Called by Timer callback after PUMP_CIRCULATION_DELAY_SECONDS.
        Verifies pump is still running before starting heater.
        """
        # Verify pump still running (could have been stopped during delay)
        if not self.pump.isOn():
            logging.error("Automations: Pump not running after delay - heater NOT started")
            Event.logOpaqueEvent("automation_heater_blocked",
                                {"reason": "pump_stopped_during_delay"})
            return

        # Start heater (with its own safety checks)
        logging.info("Automations: Starting heater after circulation established")
        if self.heater.on():  # Returns True on success
            self.heater.setModeReachTempAndStop(targetTemp)
            Event.logOpaqueEvent("automation_heating_started",
                                {"target_temp": targetTemp})
        else:
            logging.error("Automations: Heater failed to start")

    def setPumpRunForXMinutesMessageHandler(self, data):
        payload = json.loads(data)
        logging.info("setPumpRunForXMinutesMessageHandler payload: " + json.dumps(payload))
        logging.info("setPumpRunForXMinutesMessageHandler mode: " + payload['mode'])

        if payload['mode'] == "ON":
            onDurationInMinutes = int(payload['durationInMinutes'])
            self.pump.setRunForXMinutesAndStop(onDurationInMinutes)
            return

        self.pump.setModeOff();


