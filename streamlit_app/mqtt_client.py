"""
MQTT Client wrapper for PiPool Streamlit application.
Handles connection, subscriptions, and message routing in a background thread.
"""
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime
from typing import Callable, Dict, Optional

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTClient:
    """Thread-safe MQTT client for PiPool control and monitoring."""

    def __init__(self, broker_host: str, broker_port: int = 1883):
        """
        Initialize MQTT client.

        Args:
            broker_host: MQTT broker hostname or IP address
            broker_port: MQTT broker port (default: 1883)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port

        # MQTT client setup
        self.client = mqtt.Client(client_id="pipool_streamlit", protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Thread-safe state
        self._lock = threading.Lock()
        self._connected = False
        self._last_heartbeat = None

        # Data storage
        self.sensor_data: Dict = {}
        self.sensor_history: deque = deque(maxlen=300)  # Keep last 5 minutes at 1Hz
        self.mqtt_log: deque = deque(maxlen=50)  # Last 50 messages

        # Background thread
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            with self._lock:
                self._connected = True

            # Subscribe to all status topics
            client.subscribe("pipool/status")
            client.subscribe("pipool/sensors")
            logger.info("Subscribed to pipool/status and pipool/sensors")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            with self._lock:
                self._connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")
        with self._lock:
            self._connected = False

    def _on_message(self, client, userdata, msg):
        """Callback when message received from MQTT broker."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            timestamp = datetime.now()

            # Log message
            with self._lock:
                self.mqtt_log.append({
                    "timestamp": timestamp,
                    "topic": topic,
                    "payload": payload
                })

            # Handle different topics
            if topic == "pipool/status":
                with self._lock:
                    self._last_heartbeat = timestamp

            elif topic == "pipool/sensors":
                try:
                    sensor_data = json.loads(payload)
                    with self._lock:
                        self.sensor_data = sensor_data
                        # Add to history with timestamp
                        history_entry = sensor_data.copy()
                        history_entry["timestamp"] = timestamp
                        self.sensor_history.append(history_entry)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse sensor JSON: {e}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def start(self):
        """Start MQTT client in background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("MQTT client already running")
            return

        self._stop_event.clear()

        def run():
            try:
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()

                # Keep thread alive
                while not self._stop_event.is_set():
                    time.sleep(0.1)

                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT client stopped")

            except Exception as e:
                logger.error(f"MQTT client error: {e}", exc_info=True)
                with self._lock:
                    self._connected = False

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        logger.info("MQTT client thread started")

    def stop(self):
        """Stop MQTT client and background thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def publish(self, topic: str, payload: str, qos: int = 0):
        """
        Publish message to MQTT topic.

        Args:
            topic: MQTT topic to publish to
            payload: Message payload (string)
            qos: Quality of Service level (0, 1, or 2)
        """
        try:
            result = self.client.publish(topic, payload, qos=qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: {payload}")
            else:
                logger.error(f"Failed to publish to {topic}, error code: {result.rc}")
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}", exc_info=True)

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        with self._lock:
            return self._connected

    @property
    def last_heartbeat(self) -> Optional[datetime]:
        """Get timestamp of last heartbeat message."""
        with self._lock:
            return self._last_heartbeat

    def get_sensor_data(self) -> Dict:
        """Get latest sensor data (thread-safe)."""
        with self._lock:
            return self.sensor_data.copy()

    def get_sensor_history(self) -> list:
        """Get sensor history (thread-safe)."""
        with self._lock:
            return list(self.sensor_history)

    def get_mqtt_log(self) -> list:
        """Get MQTT message log (thread-safe)."""
        with self._lock:
            return list(self.mqtt_log)

    # Control methods
    def set_pump_state(self, state: str):
        """Set pump ON or OFF."""
        self.publish("pipool/control/pump_state", state)

    def set_pump_timer(self, duration_minutes: Optional[int]):
        """Start pump timer or cancel."""
        if duration_minutes is None:
            payload = json.dumps({"mode": "OFF"})
        else:
            payload = json.dumps({"mode": "ON", "durationInMinutes": duration_minutes})
        self.publish("pipool/control/pump_run_for_x_minutes", payload)

    def set_heater_state(self, state: str):
        """Set heater ON or OFF."""
        self.publish("pipool/control/heater_state", state)

    def set_heater_target(self, target_temp: Optional[float]):
        """Start heater to target temperature or cancel."""
        if target_temp is None:
            payload = json.dumps({"mode": "OFF"})
        else:
            payload = json.dumps({"mode": "ON", "targetTemp": target_temp})
        self.publish("pipool/control/heater_reach_and_stop", payload)

    def set_light_state(self, state: str):
        """Set light ON or OFF."""
        self.publish("pipool/control/light_state", state)

    def set_light_color(self, color_index: int):
        """Set light color/show (0-16)."""
        self.publish("pipool/control/light_set_color", str(color_index))
