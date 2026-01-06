# PiPool Dashboard - UI Guide

## Visual Layout Overview

This guide describes the user interface layout and components of the PiPool Streamlit Dashboard.

## Page Layout

### 1. Header Section
```
┌─────────────────────────────────────────────────────────────┐
│ 🏊 PiPool Control Dashboard                                 │
├─────────────────────────────────────────────────────────────┤
│ System Status: 🟢 Online | Last Update: 14:23:45            │
│ MQTT: 🟢 Connected      | [🔄 Refresh]                      │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- Title with pool emoji
- System status indicator (green/orange/red dot)
- Last update timestamp
- MQTT connection status
- Manual refresh button

---

### 2. Sensor Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Sensor Dashboard                                          │
├─────────────────────────────────────────────────────────────┤
│  🌡️ Water Intake   🌡️ Water Output   🌡️ Ambient   💻 RPi CPU │
│     24.5°C           25.2°C            22.0°C      45.3°C   │
│                      +0.7°C                       Normal    │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- Four metric cards in columns
- Temperature values with 1 decimal place
- Delta showing output vs. intake temperature difference
- CPU temperature with warning if >70°C

---

### 3. Device Status Overview
```
┌─────────────────────────────────────────────────────────────┐
│ 🎛️ Device Status                                            │
├─────────────────────────────────────────────────────────────┤
│    🟢 Pump          🔴 Heater         🟡 Light              │
│   Status: ON      Status: OFF       Status: ON             │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- Three device cards in columns
- Color-coded indicator (green=ON, white/gray=OFF)
- Device name and current status

**Safety Warning (when applicable):**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ SAFETY WARNING: Heater is ON but pump is OFF!            │
│    This is dangerous.                                        │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Control Panels (Tabbed Interface)

#### Tab 1: 💧 Pump Control
```
┌─────────────────────────────────────────────────────────────┐
│ Manual Control              │ Timed Run                     │
├─────────────────────────────┼───────────────────────────────┤
│ [✅ Turn ON] [⛔ Turn OFF]  │ Duration: [  30  ] minutes    │
│                             │ [⏱️ Start Timer] [🛑 Cancel]   │
└─────────────────────────────────────────────────────────────┘
```

#### Tab 2: 🔥 Heater Control
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Pump must be ON before operating heater (safety feature) │
├─────────────────────────────────────────────────────────────┤
│ Manual Control              │ Heat to Target                │
├─────────────────────────────┼───────────────────────────────┤
│ [✅ Turn ON] [⛔ Turn OFF]  │ Target Temp: [ 28.0 ] °C      │
│ (disabled if pump OFF)      │ [🎯 Start Heating] [🛑 Cancel] │
└─────────────────────────────────────────────────────────────┘
```

**High Temperature Warning:**
```
⚠️ High temperature warning: >35°C may be unsafe
```

#### Tab 3: 💡 Light Control
```
┌─────────────────────────────────────────────────────────────┐
│ Power Control               │ Color/Show Selection          │
├─────────────────────────────┼───────────────────────────────┤
│ [✅ Turn ON] [⛔ Turn OFF]  │ [Dropdown: 0: Fast Color Wash]│
│                             │ ████████████████████ (preview)│
│                             │ [🎨 Set Color]                │
└─────────────────────────────────────────────────────────────┘
```

**Light Color Options (17 total):**
- 0: Fast Color Wash
- 1: Deep Blue Sea
- 2: Royal Blue
- 3: Afternoon Skies
- 4: Aqua Green
- 5: Emerald
- 6: Cloud White
- 7: Warm Red
- 8: Flamingo
- 9: Vivid Violet
- 10: Sangria
- 11: Slow Color Wash
- 12: Blue/Cyan/White Fade
- 13: Blue/Green/Magenta Fade
- 14: Red/White/Blue Switch
- 15: Fast Random Fade - Mardi Gras
- 16: Fast Random Fade - Cool Cabaret

---

### 5. Temperature History Graph
```
┌─────────────────────────────────────────────────────────────┐
│ 📈 Temperature History                                       │
├─────────────────────────────────────────────────────────────┤
│ 30°C ┤                                ╭─ Water Output       │
│      │                            ╭───╯                     │
│ 25°C ┤    ╭─ Water Intake    ╭───╯                          │
│      │╭───╯              ╭───╯                              │
│ 20°C ┼────────────────────── Ambient                        │
│      │                                                      │
│ 15°C ┤                                                      │
│      └──────────────────────────────────────────────────    │
│        14:20    14:21    14:22    14:23    14:24           │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Interactive Plotly chart (zoom, pan, hover)
- Four temperature traces (different colors)
- Legend showing all sensors
- Dark theme matching overall UI
- Unified hover mode for easy comparison

---

### 6. MQTT Activity Log (Expandable)
```
┌─────────────────────────────────────────────────────────────┐
│ ▼ 📜 MQTT Activity Log                                      │
├─────────────────────────────────────────────────────────────┤
│ [14:23:45.123] pipool/sensors: {"temp_sensor_in": 24.5...} │
│ [14:23:45.089] pipool/status: Online                       │
│ [14:23:44.145] pipool/sensors: {"temp_sensor_in": 24.4...} │
│ [14:23:44.098] pipool/status: Online                       │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Last 20 messages displayed
- Reverse chronological order (newest first)
- Timestamp in HH:MM:SS.mmm format
- Topic and payload shown
- Long payloads truncated (>100 chars)

---

## Color Scheme

### Theme Colors
- **Background**: Dark gray (#0E1117)
- **Secondary Background**: Lighter gray (#262730)
- **Primary Accent**: Pool blue (#00BCD4)
- **Text**: Off-white (#FAFAFA)

### Status Colors
- **Green** 🟢: Device ON, System Online, Connected
- **Red** 🔴: Device OFF (critical), System Offline, Error
- **Orange** 🟠: Degraded status, Warning
- **Yellow** 🟡: Light ON, Caution
- **White/Gray** ⚪: Device OFF (normal state)

### Light Color Previews
Each light color option shows a colored bar preview:
- Deep Blue Sea: Dark blue (#1E3A8A)
- Royal Blue: Medium blue (#3B82F6)
- Aqua Green: Teal (#10B981)
- Warm Red: Red (#DC2626)
- etc. (17 total colors)

---

## Interaction Patterns

### Button States
- **Enabled**: Full opacity, clickable
- **Disabled**: Grayed out, not clickable (e.g., heater ON when pump OFF)
- **Clicked**: Shows success message below button

### Success Messages
After clicking a control button:
```
✅ Pump ON command sent
✅ Heater target set: 28.0°C
✅ Light color set: Deep Blue Sea
```

### Warning Messages
When conditions are unsafe:
```
⚠️ Pump must be ON before operating heater
⚠️ High temperature warning: >35°C may be unsafe
```

### Error Messages
When data is unavailable:
```
⚠️ No sensor data available. Waiting for MQTT messages...
```

---

## Responsive Behavior

### Desktop (Wide Screen)
- 4 columns for sensor metrics
- 3 columns for device status
- 2 columns for control panels
- Full-width temperature graph

### Tablet (Medium Screen)
- 2 columns for sensor metrics
- 2 columns for device status
- 1 column for control panels (stacked)
- Full-width temperature graph

### Mobile (Narrow Screen)
- 1 column for all components
- Stacked vertical layout
- Full-width controls
- Full-width graph with scrollable X-axis

---

## Auto-Refresh Behavior

The dashboard automatically refreshes every **2 seconds** to show real-time updates:

- Sensor values update
- Device states update
- Temperature graph extends
- MQTT log appends new messages
- Connection status checked

Manual refresh available via 🔄 button in header.

---

## Keyboard Shortcuts

Streamlit provides default shortcuts:
- **R**: Rerun/refresh the app
- **Ctrl+Shift+R**: Clear cache and refresh
- **F**: Full-screen mode (on charts)

---

## Accessibility Features

- High contrast dark theme
- Clear visual indicators (colors + text)
- Large clickable buttons
- Readable font sizes
- Logical tab order
- Screen reader compatible

---

## Tips for Best Experience

1. **Keep browser window open** for continuous monitoring
2. **Use full-screen mode** for multi-hour monitoring sessions
3. **Check MQTT log** if controls don't seem to work
4. **Watch temperature graph** for trends over time
5. **Verify pump is ON** before operating heater
6. **Use timer for pump** to avoid forgetting it on
7. **Set target temp** instead of manual heater control for efficiency

---

## Troubleshooting Visual Indicators

### System Status Indicators

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 🟢 Online | System healthy, receiving heartbeats | None needed |
| 🟠 Degraded | Heartbeat delayed 5-30 seconds | Check network |
| 🔴 Offline | No heartbeat >30 seconds | Check PiPool app |

### Device Status Indicators

| Indicator | Meaning | State |
|-----------|---------|-------|
| 🟢 | Device ON | Active |
| ⚪ | Device OFF | Inactive |
| 🔴 | Heater ON (critical device) | Active |
| 🟡 | Light ON | Active |

### MQTT Connection

| Indicator | Meaning |
|-----------|---------|
| 🟢 Connected | MQTT broker reachable |
| 🔴 Disconnected | Cannot reach broker |

---

This UI guide provides a complete visual reference for the PiPool Dashboard interface.
