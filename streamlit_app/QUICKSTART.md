# PiPool Dashboard - Quick Start Guide

## Installation (One-time Setup)

```bash
# Navigate to streamlit app directory
cd /export/workspace/pi-pool/streamlit_app

# Install dependencies with uv (recommended)
uv sync

# OR install with pip (fallback)
pip install -r requirements.txt
```

## Running the Dashboard

### Option 1: Using the startup script (easiest)

```bash
./run_streamlit.sh
```

### Option 2: Using streamlit directly

```bash
streamlit run app.py
```

### Option 3: With custom MQTT broker

```bash
MQTT_BROKER_HOST=192.168.1.100 MQTT_BROKER_PORT=1883 streamlit run app.py
```

## Access the Dashboard

Once started, open your browser to:
- **Local**: http://localhost:8501
- **Network**: http://<your-ip>:8501

## Features at a Glance

### Monitoring
- 🌡️ Real-time temperature sensors (4 sensors)
- 📊 Temperature history graphs
- 🎛️ Device status (pump, heater, light)
- 💚 System health indicator

### Controls
- **Pump**: ON/OFF, timed run (1-480 minutes)
- **Heater**: ON/OFF, heat to target (20-40°C)
- **Light**: ON/OFF, 17 color/show options

### Safety
- ⚠️ Prevents heater operation without pump
- 🌡️ High temperature warnings
- 📜 MQTT activity log for debugging

## Troubleshooting

### Dashboard shows "Offline" or "No sensor data"

1. **Check MQTT broker is running:**
   ```bash
   systemctl status mosquitto
   ```

2. **Check PiPool application is running:**
   ```bash
   ps aux | grep pipool
   ```

3. **Test MQTT connectivity:**
   ```bash
   mosquitto_sub -h 192.168.1.23 -t "pipool/sensors"
   ```

### Cannot connect to MQTT broker

1. **Verify broker host/port:**
   ```bash
   echo $MQTT_BROKER_HOST
   echo $MQTT_BROKER_PORT
   ```

2. **Check network connectivity:**
   ```bash
   ping 192.168.1.23
   ```

3. **Verify firewall allows port 1883:**
   ```bash
   sudo ufw status
   ```

### Temperature graphs not showing

- Requires at least 2 sensor readings
- Wait 2-3 seconds for data to accumulate
- Check MQTT log (expandable section at bottom)

## Development Mode

Run with auto-reload on file changes:

```bash
streamlit run app.py --server.runOnSave=true
```

## Customization

Edit `.streamlit/config.toml` to change theme colors:

```toml
[theme]
primaryColor = "#00BCD4"  # Change this for different accent color
```

## Stopping the Dashboard

Press `Ctrl+C` in the terminal where Streamlit is running.

## Next Steps

- Bookmark the dashboard URL for easy access
- Check the full README.md for detailed documentation
- Monitor the MQTT activity log to understand system behavior
- Experiment with pump timers and heater targets

Enjoy your PiPool control dashboard! 🏊
