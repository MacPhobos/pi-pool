# PiPool Streamlit Control Dashboard

Professional web interface for monitoring and controlling the PiPool automation system via MQTT.

## Features

- **Real-time Monitoring**
  - Live sensor data dashboard (water intake/output, ambient, RPi CPU temperature)
  - Temperature history graphs with Plotly
  - Device status indicators (pump, heater, light)
  - System health and MQTT connection status

- **Device Control**
  - **Pump**: Manual ON/OFF, timed run (1-480 minutes)
  - **Heater**: Manual ON/OFF, heat to target temperature (20-40°C)
  - **Light**: Manual ON/OFF, color/show selection (17 options)

- **Safety Features**
  - Warning when heater is ON but pump is OFF
  - Disable heater controls when pump is OFF
  - High temperature warnings (>35°C)
  - Visual alerts for dangerous conditions

- **Professional UI**
  - Dark theme with pool blue accents
  - Responsive card-based layout
  - Real-time auto-refresh (2-second interval)
  - MQTT activity log
  - Clean, intuitive controls

## Installation

### 1. Install Dependencies

```bash
cd streamlit_app
uv sync
```

Or using pip (fallback):

```bash
pip install -r requirements.txt
```

### 2. Configure MQTT Broker

Set environment variables (optional, defaults to 192.168.1.23:1883):

```bash
export MQTT_BROKER_HOST=192.168.1.23
export MQTT_BROKER_PORT=1883
```

## Running the Application

### Using Streamlit CLI

```bash
cd streamlit_app
streamlit run app.py
```

### Using the Startup Script

```bash
./run_streamlit.sh
```

The application will be available at:
- Local: http://localhost:8501
- Network: http://<your-ip>:8501

## MQTT Topics

### Subscribed Topics (status/telemetry)
- `pipool/status` - System heartbeat ("Online" every second)
- `pipool/sensors` - JSON sensor data (temperatures, device states)

### Published Topics (control)
- `pipool/control/pump_state` - `"ON"` / `"OFF"`
- `pipool/control/pump_run_for_x_minutes` - JSON with duration
- `pipool/control/heater_state` - `"ON"` / `"OFF"`
- `pipool/control/heater_reach_and_stop` - JSON with target temperature
- `pipool/control/light_state` - `"ON"` / `"OFF"`
- `pipool/control/light_set_color` - `"0"` to `"16"` (color index)

## Architecture

```
streamlit_app/
├── app.py                  # Main Streamlit application
├── mqtt_client.py          # MQTT client wrapper with threading
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Dark theme configuration
└── README.md              # This file
```

### MQTT Client (`mqtt_client.py`)
- Thread-safe MQTT client wrapper
- Background thread for message loop
- Maintains sensor history (last 300 readings)
- Provides control methods for all devices

### Streamlit App (`app.py`)
- Modular component rendering
- Real-time data visualization with Plotly
- Session state management
- Auto-refresh every 2 seconds

## Configuration

### Environment Variables

- `MQTT_BROKER_HOST` - MQTT broker hostname/IP (default: `192.168.1.23`)
- `MQTT_BROKER_PORT` - MQTT broker port (default: `1883`)

### Theme Customization

Edit `.streamlit/config.toml` to customize colors and theme:

```toml
[theme]
primaryColor = "#00BCD4"      # Pool blue accent
backgroundColor = "#0E1117"    # Dark background
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
```

## Development

### Running in Development Mode

```bash
# With auto-reload on file changes
streamlit run app.py --server.runOnSave=true
```

### Testing Without Hardware

The app will gracefully handle missing MQTT messages and display "No sensor data available" warnings.

### Debugging MQTT

Monitor MQTT messages from command line:

```bash
# Monitor all pipool topics
mosquitto_sub -h 192.168.1.23 -t "pipool/#"

# Monitor only sensors
mosquitto_sub -h 192.168.1.23 -t "pipool/sensors"
```

## Troubleshooting

### "No sensor data available"
- Check MQTT broker is running: `systemctl status mosquitto`
- Verify PiPool main application is running
- Check broker host/port configuration

### MQTT connection fails
- Verify network connectivity to broker
- Check firewall rules (port 1883)
- Ensure broker allows anonymous connections or configure credentials

### Temperature graphs not updating
- Data collection requires 2+ sensor readings
- Check MQTT client is connected (green indicator in header)
- Verify `pipool/sensors` topic is publishing data

## Safety Notes

⚠️ **IMPORTANT SAFETY FEATURES:**

1. **Heater-Pump Interlock**: Heater controls are disabled when pump is OFF
2. **Visual Warnings**: Red alert displayed if heater ON without pump
3. **Temperature Limits**: Warnings for temperatures >35°C
4. **Graceful Degradation**: UI handles missing data and connection failures

This application is designed for safe operation of pool equipment. Always verify physical equipment state matches dashboard status.

## License

Part of the PiPool project. See main repository for license information.
