#!/bin/bash
# Startup script for PiPool Streamlit Dashboard

# Set default MQTT broker if not configured
export MQTT_BROKER_HOST=${MQTT_BROKER_HOST:-192.168.1.23}
export MQTT_BROKER_PORT=${MQTT_BROKER_PORT:-1883}

echo "==================================="
echo "PiPool Streamlit Control Dashboard"
echo "==================================="
echo "MQTT Broker: ${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}"
echo ""
echo "Starting Streamlit application..."
echo "Access at: http://localhost:8501"
echo "==================================="

# Change to script directory
cd "$(dirname "$0")"

# Run Streamlit with uv
uv run streamlit run app.py
