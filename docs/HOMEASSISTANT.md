# Home Assistant Integration Guide

This guide explains how to integrate PiPool with Home Assistant using MQTT for real-time monitoring and control of your pool equipment.

## Overview

PiPool publishes sensor data and device states to MQTT topics, and subscribes to control topics for commands. Home Assistant connects to the same MQTT broker to receive updates and send control commands.

```
┌─────────────┐     MQTT      ┌─────────────────┐     MQTT      ┌────────────────┐
│   PiPool    │◄────────────► │   MQTT Broker   │◄────────────► │ Home Assistant │
│ (Raspberry  │  pipool/#     │  (Mosquitto)    │  pipool/#     │                │
│    Pi)      │               │                 │               │                │
└─────────────┘               └─────────────────┘               └────────────────┘
```

## Prerequisites

Before configuring Home Assistant, ensure:

1. **PiPool is running** and publishing to MQTT (verify with `mosquitto_sub -h <broker> -t "pipool/#"`)
2. **MQTT broker is accessible** from both PiPool and Home Assistant (typically Mosquitto)
3. **Home Assistant MQTT integration** is installed and configured

## Step 1: Configure MQTT Integration in Home Assistant

If you haven't already set up MQTT in Home Assistant:

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "MQTT" and select it
3. Enter your MQTT broker details:
   - **Broker**: IP address or hostname of your MQTT broker (e.g., `192.168.1.100` or `localhost`)
   - **Port**: `1883` (default) or `8883` for TLS
   - **Username/Password**: If your broker requires authentication
4. Click **Submit** to complete setup

### Verify MQTT Connection

To verify Home Assistant can see PiPool messages:
1. Go to **Settings** → **Devices & Services** → **MQTT**
2. Click **Configure** → **Listen to a topic**
3. Enter `pipool/#` and click **Start Listening**
4. You should see sensor data appearing every few seconds

## Step 2: Add MQTT Entities to Configuration

Home Assistant needs entity definitions to interpret MQTT messages. Add the following to your `configuration.yaml` file.

> **Note**: If you use split configuration files, you can place the `mqtt:` section in a separate file like `mqtt.yaml` and include it with `mqtt: !include mqtt.yaml`.

### Sensor Configuration

These sensors read data published by PiPool to the `pipool/sensors` topic:

```yaml
mqtt:
  sensor:
    - name: "POOL - Temp - Intake"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.temp_sensor_in }}'
      unit_of_measurement: 'C'

    - name: "POOL - Temp - Output"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.temp_sensor_out }}'
      unit_of_measurement: 'C'

    - name: "POOL - Temp - RPI"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.temp_rpi }}'
      unit_of_measurement: 'C'

    - name: "POOL - Temp - Enclosure"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.temp_ambient }}'
      unit_of_measurement: 'C'

    - name: "POOL - Sensor - Pump State"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.pump_state }}'

    - name: "POOL - Sensor - Heater State"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.heater_state }}'

    - name: "POOL - Sensor - Light State"
      state_topic: "pipool/sensors"
      value_template: '{{ value_json.light_state }}'
```

### Switch Configuration

These switches allow you to control pool equipment. Each switch has:
- **command_topic**: Where Home Assistant sends ON/OFF commands
- **state_topic**: Where PiPool publishes the actual device state

#### Basic Device Control

Simple ON/OFF switches for pump, heater, and light:

```yaml
  switch:
    - name: "POOL Pump"
      command_topic: "pipool/control/pump_state"
      state_topic: 'pipool/state/pump_state'
      device_class: switch
      retain: false
      optimistic: false
      payload_on: "ON"
      payload_off: "OFF"
      state_on: "ON"
      state_off: "OFF"
      qos: 0
    - name: "POOL Heater"
      command_topic: "pipool/control/heater_state"
      state_topic: 'pipool/state/heater_state'
      retain: true
      optimistic: false
      payload_on: "ON"
      payload_off: "OFF"
    - name: "POOL Light"
      command_topic: "pipool/control/light_state"
      state_topic: 'pipool/state/light_state'
      retain: true
      optimistic: false
      payload_on: "ON"
      payload_off: "OFF"
```

#### Target Temperature Heater Control

These switches turn on the heater and automatically stop when the target temperature is reached. The pump must be running for the heater to operate (safety interlock).

```yaml
    - name: "POOL Heater - Hit 25"
      command_topic: "pipool/control/heater_reach_and_stop"
      state_topic: 'pipool/state/heater_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "targetTemp": 25 }'
      payload_off: '{ "mode": "OFF", "targetTemp": 0 }'

    - name: "POOL Heater - Hit 27"
      command_topic: "pipool/control/heater_reach_and_stop"
      state_topic: 'pipool/state/heater_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "targetTemp": 27 }'
      payload_off: '{ "mode": "OFF", "targetTemp": 0 }'


    - name: "POOL Heater - Hit 29"
      command_topic: "pipool/control/heater_reach_and_stop"
      state_topic: 'pipool/state/heater_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "targetTemp": 29 }'
      payload_off: '{ "mode": "OFF", "targetTemp": 0 }'

    - name: "POOL Heater - Hit 31"
      command_topic: "pipool/control/heater_reach_and_stop"
      state_topic: 'pipool/state/heater_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "targetTemp": 31 }'
      payload_off: '{ "mode": "OFF", "targetTemp": 0 }'
```

#### Timed Pump Control

These switches run the pump for a specified duration and then automatically turn off. Useful for circulation or filtering cycles.

```yaml
    - name: "POOL Pump - 1 minute"
      command_topic: "pipool/control/pump_run_for_x_minutes"
      state_topic: 'pipool/state/pump_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "durationInMinutes": 1 }'
      payload_off: '{ "mode": "OFF", "durationInMinutes": 0 }'

    - name: "POOL Pump - 5 minute"
      command_topic: "pipool/control/pump_run_for_x_minutes"
      state_topic: 'pipool/state/pump_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "durationInMinutes": 5 }'
      payload_off: '{ "mode": "OFF", "durationInMinutes": 0 }'

    - name: "POOL Pump - 10 minute"
      command_topic: "pipool/control/pump_run_for_x_minutes"
      state_topic: 'pipool/state/pump_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "durationInMinutes": 10 }'
      payload_off: '{ "mode": "OFF", "durationInMinutes": 0 }'

    - name: "POOL Pump - 20 minute"
      command_topic: "pipool/control/pump_run_for_x_minutes"
      state_topic: 'pipool/state/pump_state'
      retain: false
      optimistic: false
      payload_on:  '{ "mode": "ON", "durationInMinutes": 20 }'
      payload_off: '{ "mode": "OFF", "durationInMinutes": 0 }'
```

#### Pool Light Color Selection

These switches cycle the pool light to a specific color/mode. The light uses power cycling to select colors (similar to many color-changing pool lights). The "Color - Reset" option resets the light to its default state.

> **Note**: These are momentary switches - they send a command to cycle to that color but don't maintain state.

```yaml
    - name: "Color 0 - Fast Wash"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "0"
      payload_off: "0"
      qos: 0
    - name: "Color 1 - Deep Blue Sea"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "1"
      payload_off: "1"
      qos: 0
    - name: "Color 2 - Royal Blue"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "2"
      payload_off: "2"
      qos: 0
    - name: "Color 3 - Afternoon Skies"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "3"
      payload_off: "3"
      qos: 0
    - name: "Color 4 - Aqua Green"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "4"
      payload_off: "4"
      qos: 0
    - name: "Color 5 - Emerald"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "5"
      payload_off: "5"
      qos: 0
    - name: "Color 6 - Cloud White"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "6"
      payload_off: "6"
      qos: 0
    - name: "Color 7 - Warm Red"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "7"
      payload_off: "7"
      qos: 0
    - name: "Color 8 - Flamingo"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "8"
      payload_off: "8"
      qos: 0
    - name: "Color 9 - Vivid Violet"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "9"
      payload_off: "9"
      qos: 0
    - name: "Color 10 - Sangria"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "10"
      payload_off: "10"
      qos: 0
    - name: "Color 11 - Slow Wash"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "11"
      payload_off: "11"
      qos: 0
    - name: "Color 12 - White Fade"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "12"
      payload_off: "12"
      qos: 0
    - name: "Color 13 - Magenta Fade"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "13"
      payload_off: "13"
      qos: 0
    - name: "Color 14 - Blue Switch"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "14"
      payload_off: "14"
      qos: 0
    - name: "Color 15 - Mardi Gras - Random Fade"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "15"
      payload_off: "15"
      qos: 0
    - name: "Color 16 - Cool Cabaret - Random Fade"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "16"
      payload_off: "16"
      qos: 0
    - name: "Color - Reset"
      command_topic: "pipool/control/light_set_color"
      retain: false
      payload_on:  "1000"
      payload_off: "1000"
      qos: 0
```

## Step 3: Restart Home Assistant

After adding the configuration:

1. **Check Configuration**: Go to **Developer Tools** → **YAML** → **Check Configuration**
2. If valid, click **Restart** → **Restart Home Assistant**
3. Wait for Home Assistant to fully restart (1-2 minutes)

## Step 4: Verify Entities

After restart, verify your new entities:

1. Go to **Developer Tools** → **States**
2. Filter for "pool" - you should see all the sensors and switches
3. Check that sensor values are updating (not "unknown" or "unavailable")

If entities show "unavailable":
- Verify PiPool is running and publishing to MQTT
- Check that the MQTT broker is reachable
- Verify topic names match exactly (case-sensitive)

## Step 5: Create a Dashboard (Optional)

You can create a custom dashboard to visualize and control your pool. Below is a sample dashboard configuration.

### Adding the Dashboard

**Option A: Using the UI**
1. Go to **Settings** → **Dashboards** → **Add Dashboard**
2. Choose "Start with an empty dashboard"
3. Click **Edit Dashboard** → three-dot menu → **Raw configuration editor**
4. Paste the YAML below

**Option B: Using YAML Mode**
Add this to your `ui-lovelace.yaml` or use it as a dashboard YAML file.

### Sample Dashboard Configuration

```yaml
title: Home
views:
  - theme: Backend-selected
    title: Pool
    path: pool
    badges: []
    cards:
      - type: entities
        entities:
          - entity: switch.pool_pump
          - entity: sensor.pool_sensor_pump_state
          - entity: switch.pool_heater
            icon: mdi:hot-tub
            name: Heater
          - entity: sensor.pool_sensor_heater_state
            icon: mdi:hot-tub
          - entity: switch.pool_light
          - entity: sensor.pool_sensor_light_state
            icon: mdi:lightbulb
          - entity: switch.pool_pump_1_minute
            name: POOL Pump - 1 min
            icon: mdi:pump
          - entity: switch.pool_pump_5_minute
            name: POOL Pump - 5 min
            icon: mdi:pump
          - entity: switch.pool_pump_10_minute
            name: POOL Pump - 10 min
            icon: mdi:pump
          - entity: switch.pool_pump_20_minute
            name: POOL Pump - 20 min
            icon: mdi:pump
          - entity: switch.pool_heater_hit_25
            icon: mdi:fire
            name: Heater Reach & Stop 25 / 77
          - entity: switch.pool_heater_hit_27
            icon: mdi:fire
            name: Heater Reach & Stop 27 / 81
          - entity: switch.pool_heater_hit_29
            name: Heater Reach & Stop 29 / 84
            icon: mdi:fire
          - entity: switch.pool_heater_hit_31
            icon: mdi:fire
            name: Heater Reach & Stop 31 / 88
      - type: vertical-stack
        cards:
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_intake
            detail: 1
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_output
            detail: 1
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_enclosure
            detail: 1
            name: Enclosure Ambient Temp
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_rpi
            detail: 1
            name: RPI CPU Temp
      - type: entities
        entities:
          - entity: switch.color_0_fast_wash
          - entity: switch.color_1_deep_blue_sea
          - entity: switch.color_2_royal_blue
          - entity: switch.color_3_afternoon_skies
          - entity: switch.color_4_aqua_green
          - entity: switch.color_5_emerald
          - entity: switch.color_6_cloud_white
          - entity: switch.color_7_warm_red
          - entity: switch.color_8_flamingo
          - entity: switch.color_9_vivid_violet
          - entity: switch.color_10_sangria
          - entity: switch.color_11_slow_wash
          - entity: switch.color_12_white_fade
          - entity: switch.color_13_magenta_fade
          - entity: switch.color_14_blue_switch
          - entity: switch.color_15_mardi_gras_random_fade_2
          - entity: switch.color_16_cool_cabaret_random_fade_2
          - entity: switch.color_reset_2
        title: Color Logic Light
        show_header_toggle: false
        state_color: true
      - type: history-graph
        entities:
          - entity: sensor.pool_sensor_pump_state
        title: Pump State History
        hours_to_show: 48
      - type: history-graph
        entities:
          - entity: sensor.pipool
        title: PiPool Connectivity
      - type: history-graph
        entities:
          - entity: sensor.pool_temp_intake
          - entity: sensor.pool_temp_output
          - entity: sensor.pool_temp_output
          - entity: sensor.pool_temp_rpi
        refresh_interval: 10
        hours_to_show: 96
  - theme: Backend-selected
    title: POOL  Graphs
    path: pool2
    icon: ''
    badges: []
    cards:
      - type: vertical-stack
        cards:
          - graph: line
            hours_to_show: 12
            type: sensor
            entity: sensor.pool_temp_intake
            detail: 2
            name: Intake (12h)
          - graph: line
            hours_to_show: 12
            type: sensor
            entity: sensor.pool_temp_output
            detail: 2
            name: Output (12h)
          - graph: line
            hours_to_show: 12
            type: sensor
            detail: 2
            name: RPI CPU Temp (12h)
            entity: sensor.pool_temp_rpi
      - type: vertical-stack
        cards:
          - graph: line
            hours_to_show: 24
            type: sensor
            detail: 2
            name: Intake (24h)
            entity: sensor.pool_temp_intake
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_output
            detail: 2
            name: Output (24h)
          - graph: line
            hours_to_show: 24
            type: sensor
            entity: sensor.pool_temp_rpi
            detail: 2
            name: RPI CPU Temp (24h)
      - show_name: true
        show_icon: true
        show_state: true
        type: glance
        entities:
          - entity: sensor.pool_temp_intake
          - entity: sensor.pool_temp_output
          - entity: sensor.pool_temp_enclosure
          - entity: sensor.pool_temp_rpi
        state_color: false
      - type: vertical-stack
        cards:
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 24
            refresh_interval: 5
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 48
            refresh_interval: 5
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 48
            refresh_interval: 5
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 96
            refresh_interval: 5
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 168
            refresh_interval: 5
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            refresh_interval: 5
            hours_to_show: 500
          - type: history-graph
            entities:
              - entity: sensor.pool_temp_intake
              - entity: sensor.pool_temp_output
              - entity: sensor.pool_temp_enclosure
            hours_to_show: 8000
            refresh_interval: 5
      - type: logbook
        entities:
          - sensor.pool_sensor_pump_state
```

## MQTT Topic Reference

PiPool uses the following MQTT topics:

### Published by PiPool (Subscribe in Home Assistant)

| Topic | Description | Payload Example |
|-------|-------------|-----------------|
| `pipool/sensors` | All sensor data (JSON) | `{"temp_sensor_in": 24.5, "pump_state": "ON", ...}` |
| `pipool/state/pump_state` | Pump state | `ON` or `OFF` |
| `pipool/state/heater_state` | Heater state | `ON` or `OFF` |
| `pipool/state/light_state` | Light state | `ON` or `OFF` |

### Subscribed by PiPool (Publish from Home Assistant)

| Topic | Description | Payload |
|-------|-------------|---------|
| `pipool/control/pump_state` | Turn pump on/off | `ON` or `OFF` |
| `pipool/control/heater_state` | Turn heater on/off | `ON` or `OFF` |
| `pipool/control/light_state` | Turn light on/off | `ON` or `OFF` |
| `pipool/control/heater_reach_and_stop` | Heat to target temp | `{"mode": "ON", "targetTemp": 27}` |
| `pipool/control/pump_run_for_x_minutes` | Run pump for duration | `{"mode": "ON", "durationInMinutes": 10}` |
| `pipool/control/light_set_color` | Set light color (0-16, 1000=reset) | `5` |

## Troubleshooting

### Entities Show "Unavailable"

1. **Check PiPool is running**:
   ```bash
   mosquitto_sub -h <broker_ip> -t "pipool/sensors"
   ```
   You should see JSON data every few seconds.

2. **Check MQTT broker connectivity** from Home Assistant host:
   ```bash
   mosquitto_sub -h <broker_ip> -t "#" -v
   ```

3. **Verify MQTT integration** in Home Assistant:
   - Go to **Settings** → **Devices & Services** → **MQTT**
   - Status should show "Connected"

### Switches Don't Control Equipment

1. **Verify PiPool receives commands**:
   ```bash
   # In one terminal, watch for commands:
   mosquitto_sub -h <broker_ip> -t "pipool/control/#" -v

   # In another terminal, send a test command:
   mosquitto_pub -h <broker_ip> -t "pipool/control/pump_state" -m "ON"
   ```

2. **Check PiPool logs** for received MQTT messages

3. **Verify topic names** match exactly (case-sensitive)

### Sensor Values Not Updating

1. **Check sensor JSON format**: The `value_template` extracts specific fields from the JSON payload. If PiPool's JSON structure changes, update the templates.

2. **Test template in Developer Tools**:
   - Go to **Developer Tools** → **Template**
   - Test your Jinja2 template with sample data

### Temperature Shows in Wrong Units

The sensors are configured for Celsius. To convert to Fahrenheit, modify the `value_template`:

```yaml
value_template: '{{ (value_json.temp_sensor_in * 9/5 + 32) | round(1) }}'
unit_of_measurement: '°F'
```

## Automations (Advanced)

You can create Home Assistant automations to control PiPool based on conditions. Examples:

### Run Pump Daily

```yaml
automation:
  - alias: "Pool Pump Daily Run"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.pool_pump_20_minute
```

### Heat Pool Before Use

```yaml
automation:
  - alias: "Heat Pool for Weekend"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: time
        weekday:
          - sat
          - sun
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.pool_heater_hit_27
```

## Additional Resources

- [Home Assistant MQTT Documentation](https://www.home-assistant.io/integrations/mqtt/)
- [MQTT Sensor Documentation](https://www.home-assistant.io/integrations/sensor.mqtt/)
- [MQTT Switch Documentation](https://www.home-assistant.io/integrations/switch.mqtt/)
- [Lovelace Dashboard Documentation](https://www.home-assistant.io/dashboards/)
