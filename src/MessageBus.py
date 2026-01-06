import logging
import paho.mqtt.client as mqtt

# Global connection state - initialized to False
flag_connected = False
messageBus = None


def on_connect(client, userdata, flags, rc):
    logging.info("MQTT: Connected with flags [%s] rtn code [%d]" % (flags, rc))
    global flag_connected
    global messageBus
    flag_connected = True
    messageBus.addSubscriptions()


def on_disconnect(client, userdata, rc):
    logging.info("MQTT: disconnected with rtn code [%d]" % rc)
    global flag_connected
    flag_connected = False


def on_message(client, userdata, message):
    logging.info("MQTT: message received = " + str(message.payload.decode("utf-8")))
    logging.info("MQTT: message topic = " + message.topic)
    logging.info("MQTT: message qos = " + str(message.qos))
    logging.info("MQTT: message retain flag = " + str(message.retain))

    payload = str(message.payload.decode("utf-8"))

    handler = userdata.handlers.get(message.topic)
    if handler is not None:
        handler(payload)
        return
    else:
        logging.error("NO HANDLER for topic: " + message.topic + " - ignoring message")
        return

class MessageBus:
    """MQTT message bus for pool automation control and monitoring.

    Provides publish-subscribe messaging for:
    - Control commands: Turn devices on/off, set modes, set temperatures
    - Status publishing: Device states, sensor readings, events
    - Remote monitoring: Real-time pool system visibility

    Topics:
    - pipool/control/* - Incoming control commands
    - pipool/status - Outgoing device status
    - pipool/sensors - Outgoing sensor data

    The MessageBus maintains persistent connection to MQTT broker with
    automatic reconnection and subscription management.

    Attributes:
        pump: Pump controller reference
        light: Light controller reference
        heater: Heater controller reference
        lightColorLogic: Light color logic reference
        mqttBroker: MQTT broker address
        client: Paho MQTT client
        handlers: Dictionary mapping topics to handler functions
    """

    def __init__(self, pump, light, heater, lightColorLogic, mqttBroker=None):
        """Initialize MQTT MessageBus.

        Args:
            pump: Pump controller instance
            light: Light controller instance
            heater: Heater controller instance
            lightColorLogic: Light color logic instance
            mqttBroker: MQTT broker address (configurable)
                        If None, uses Config.getInstance().mqttBroker
        """
        self.pump = pump
        self.light = light
        self.heater = heater
        self.lightColorLogic = lightColorLogic

        # Use configured broker address instead of hardcoded
        if mqttBroker is not None:
            self.mqttBroker = mqttBroker
        else:
            # Import here to avoid circular dependency
            from Config import Config
            self.mqttBroker = Config.getInstance().mqttBroker

        self.client = mqtt.Client(userdata=self)

        self.client.on_connect    = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_message    = on_message

        self.handlers = dict()
        global messageBus
        messageBus = self

    def addHandler(self, topic: str, handler):
        """Register a handler function for a specific MQTT topic.

        Args:
            topic: MQTT topic string (e.g., "pipool/control/pump_state")
            handler: Callable that receives payload string as parameter
        """
        logging.info("Adding handler for topic: " + topic)
        self.handlers[topic] = handler

    def start(self):
        """Start MQTT client background thread for message processing."""
        self.client.loop_start()

    def stop(self):
        """Stop MQTT client background thread."""
        self.client.loop_stop()

    def publish(self, topic, message):
        """Publish message to MQTT topic.

        Args:
            topic: MQTT topic string
            message: Message payload (string or JSON)
        """
        self.client.publish(topic, message)

    def connect(self):
        """Connect to MQTT broker using configured address."""
        try:
            self.client.connect(self.mqttBroker)
            logging.info(f"MQTT: Connection initiated to {self.mqttBroker}")
        except Exception as e:
            logging.error(f"MQTT: Connection to {self.mqttBroker} failed - {e}")


    def subscribe(self, topic):
        """Subscribe to MQTT topic.

        Args:
            topic: MQTT topic string or pattern (supports wildcards)
        """
        self.client.subscribe(topic)

    def addSubscriptions(self):
        """Subscribe to all control topics for pool automation.

        Called automatically on MQTT connection. Subscribes to topics for:
        - Pump control (state, on, off, timed operation)
        - Light control (state, color cycling, set color)
        - Heater control (state, mode, target temperature)
        """
        self.subscribe("pipool/control/pump_state")
        self.subscribe("pipool/control/pump_on")
        self.subscribe("pipool/control/pump_off")
        self.subscribe("pipool/control/light_state")
        self.subscribe("pipool/control/light_cycle")
        self.subscribe("pipool/control/heater_state")
        self.subscribe("pipool/control/heater_mode")
        self.subscribe("pipool/control/heater_target_temp")
        self.subscribe("pipool/control/heater_reach_and_stop")
        self.subscribe("pipool/control/pump_run_for_x_minutes")
        self.subscribe("pipool/control/light_set_color")

    def isConnected(self):
        """Check if MQTT client is currently connected to broker.

        Returns:
            bool: True if connected, False otherwise
        """
        global flag_connected
        return flag_connected
