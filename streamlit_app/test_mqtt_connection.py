#!/usr/bin/env python3
"""
Test MQTT connection for PiPool Streamlit Dashboard

Simple script to verify MQTT broker connectivity and message reception.
Run this before starting the dashboard to diagnose connection issues.
"""
import json
import os
import sys
import time

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        print("✅ Successfully connected to MQTT broker")
        print("   Subscribing to pipool/status and pipool/sensors...")
        client.subscribe("pipool/status")
        client.subscribe("pipool/sensors")
    else:
        print(f"❌ Failed to connect to MQTT broker, return code: {rc}")
        print("   Return codes:")
        print("   0: Connection successful")
        print("   1: Connection refused - incorrect protocol version")
        print("   2: Connection refused - invalid client identifier")
        print("   3: Connection refused - server unavailable")
        print("   4: Connection refused - bad username or password")
        print("   5: Connection refused - not authorized")


def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker."""
    print(f"⚠️ Disconnected from MQTT broker, return code: {rc}")


def on_message(client, userdata, msg):
    """Callback when message received."""
    timestamp = time.strftime("%H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    print(f"\n[{timestamp}] Message received:")
    print(f"  Topic: {topic}")

    # Pretty print JSON if applicable
    if topic == "pipool/sensors":
        try:
            sensor_data = json.loads(payload)
            print(f"  Payload (JSON):")
            for key, value in sensor_data.items():
                print(f"    {key}: {value}")
        except json.JSONDecodeError:
            print(f"  Payload: {payload}")
    else:
        print(f"  Payload: {payload}")


def main():
    """Main test function."""
    # Get broker configuration
    broker_host = os.environ.get("MQTT_BROKER_HOST", "192.168.1.23")
    broker_port = int(os.environ.get("MQTT_BROKER_PORT", "1883"))

    print("=" * 60)
    print("PiPool MQTT Connection Test")
    print("=" * 60)
    print(f"Broker: {broker_host}:{broker_port}")
    print()
    print("This script will:")
    print("  1. Connect to the MQTT broker")
    print("  2. Subscribe to pipool/status and pipool/sensors")
    print("  3. Display received messages")
    print()
    print("Press Ctrl+C to exit")
    print("=" * 60)
    print()

    # Create MQTT client
    client = mqtt.Client(client_id="pipool_test", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to broker
    print(f"Connecting to {broker_host}:{broker_port}...")
    try:
        client.connect(broker_host, broker_port, keepalive=60)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print(f"  - Verify broker is running: systemctl status mosquitto")
        print(f"  - Check network connectivity: ping {broker_host}")
        print(f"  - Verify port {broker_port} is open")
        sys.exit(1)

    # Start loop
    print("Waiting for messages... (this will run for 30 seconds)")
    print()

    try:
        client.loop_start()
        time.sleep(30)
        client.loop_stop()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        client.loop_stop()

    # Disconnect
    client.disconnect()

    print()
    print("=" * 60)
    print("Test complete!")
    print()
    print("If you saw messages above, the connection is working.")
    print("If not, check:")
    print("  - PiPool application is running")
    print("  - MQTT broker address is correct")
    print("  - Firewall allows connections to port 1883")
    print("=" * 60)


if __name__ == "__main__":
    main()
