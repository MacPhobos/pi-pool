"""
PiPool Control Dashboard - Streamlit Application

Professional web interface for monitoring and controlling a Raspberry Pi pool automation system.
Connects to PiPool MQTT broker for real-time status updates and device control.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from mqtt_client import MQTTClient

# Page configuration
st.set_page_config(
    page_title="PiPool Control Dashboard",
    page_icon="🏊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Light color definitions
LIGHT_COLORS = {
    0: "Fast Color Wash",
    1: "Deep Blue Sea",
    2: "Royal Blue",
    3: "Afternoon Skies",
    4: "Aqua Green",
    5: "Emerald",
    6: "Cloud White",
    7: "Warm Red",
    8: "Flamingo",
    9: "Vivid Violet",
    10: "Sangria",
    11: "Slow Color Wash",
    12: "Blue/Cyan/White Fade",
    13: "Blue/Green/Magenta Fade",
    14: "Red/White/Blue Switch",
    15: "Fast Random Fade - Mardi Gras",
    16: "Fast Random Fade - Cool Cabaret",
}

# Color mapping for visual representation
LIGHT_COLOR_HEX = {
    0: "#FF6B6B",  # Fast wash - red
    1: "#1E3A8A",  # Deep blue
    2: "#3B82F6",  # Royal blue
    3: "#60A5FA",  # Afternoon skies
    4: "#10B981",  # Aqua green
    5: "#059669",  # Emerald
    6: "#F3F4F6",  # Cloud white
    7: "#DC2626",  # Warm red
    8: "#F472B6",  # Flamingo
    9: "#8B5CF6",  # Vivid violet
    10: "#991B1B",  # Sangria
    11: "#EC4899",  # Slow wash - magenta
    12: "#06B6D4",  # Blue/Cyan/White
    13: "#A855F7",  # Blue/Green/Magenta
    14: "#EF4444",  # Red/White/Blue
    15: "#F59E0B",  # Mardi Gras
    16: "#EC4899",  # Cool Cabaret
}


@st.cache_resource
def get_mqtt_client():
    """Create and start MQTT client (singleton)."""
    broker_host = os.environ.get("MQTT_BROKER_HOST", "192.168.1.23")
    broker_port = int(os.environ.get("MQTT_BROKER_PORT", "1883"))

    client = MQTTClient(broker_host, broker_port)
    client.start()
    return client


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = datetime.now()


def get_system_status(mqtt_client: MQTTClient) -> dict:
    """
    Determine overall system status based on heartbeat and sensor data.

    Returns:
        dict with 'status' (Online/Offline), 'color', and 'last_update'
    """
    last_heartbeat = mqtt_client.last_heartbeat

    if last_heartbeat is None:
        return {
            "status": "Offline",
            "color": "red",
            "last_update": "Never",
        }

    time_since_heartbeat = datetime.now() - last_heartbeat

    if time_since_heartbeat < timedelta(seconds=5):
        return {
            "status": "Online",
            "color": "green",
            "last_update": last_heartbeat.strftime("%H:%M:%S"),
        }
    elif time_since_heartbeat < timedelta(seconds=30):
        return {
            "status": "Degraded",
            "color": "orange",
            "last_update": last_heartbeat.strftime("%H:%M:%S"),
        }
    else:
        return {
            "status": "Offline",
            "color": "red",
            "last_update": last_heartbeat.strftime("%H:%M:%S"),
        }


def render_header(mqtt_client: MQTTClient):
    """Render application header with status."""
    st.title("🏊 PiPool Control Dashboard")

    # Status bar
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    system_status = get_system_status(mqtt_client)

    with col1:
        status_color = system_status["color"]
        status_text = system_status["status"]
        st.markdown(
            f"**System Status:** <span style='color:{status_color}'>●</span> {status_text}",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(f"**Last Update:** {system_status['last_update']}")

    with col3:
        connection_status = "🟢 Connected" if mqtt_client.is_connected else "🔴 Disconnected"
        st.markdown(f"**MQTT:** {connection_status}")

    with col4:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()

    st.divider()


def render_sensor_dashboard(mqtt_client: MQTTClient):
    """Render sensor metrics dashboard."""
    st.subheader("📊 Sensor Dashboard")

    sensor_data = mqtt_client.get_sensor_data()

    if not sensor_data:
        st.warning("No sensor data available. Waiting for MQTT messages...")
        return

    # Four temperature metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        temp_in = sensor_data.get("temp_sensor_in", 0.0)
        st.metric(
            label="🌡️ Water Intake",
            value=f"{temp_in:.1f}°C",
            delta=None,
        )

    with col2:
        temp_out = sensor_data.get("temp_sensor_out", 0.0)
        temp_delta = temp_out - temp_in if temp_in > 0 else None
        st.metric(
            label="🌡️ Water Output",
            value=f"{temp_out:.1f}°C",
            delta=f"{temp_delta:+.1f}°C" if temp_delta is not None else None,
        )

    with col3:
        temp_ambient = sensor_data.get("temp_ambient", 0.0)
        st.metric(
            label="🌡️ Ambient",
            value=f"{temp_ambient:.1f}°C",
            delta=None,
        )

    with col4:
        rpi_temp = sensor_data.get("rpi_cpu_temp", 0.0)
        # Warn if CPU temp above 70°C
        rpi_delta = None
        if rpi_temp > 70:
            rpi_delta = "⚠️ High"
        st.metric(
            label="💻 RPi CPU",
            value=f"{rpi_temp:.1f}°C",
            delta=rpi_delta,
        )


def render_device_status(mqtt_client: MQTTClient):
    """Render device status cards."""
    st.subheader("🎛️ Device Status")

    sensor_data = mqtt_client.get_sensor_data()

    col1, col2, col3 = st.columns(3)

    pump_state = sensor_data.get("pump_state", "UNKNOWN")
    heater_state = sensor_data.get("heater_state", "UNKNOWN")
    light_state = sensor_data.get("light_state", "UNKNOWN")

    with col1:
        pump_color = "🟢" if pump_state == "ON" else "⚪"
        st.markdown(f"### {pump_color} Pump")
        st.markdown(f"**Status:** `{pump_state}`")

    with col2:
        heater_color = "🔴" if heater_state == "ON" else "⚪"
        st.markdown(f"### {heater_color} Heater")
        st.markdown(f"**Status:** `{heater_state}`")

    with col3:
        light_color = "🟡" if light_state == "ON" else "⚪"
        st.markdown(f"### {light_color} Light")
        st.markdown(f"**Status:** `{light_state}`")

    # Safety warning
    if heater_state == "ON" and pump_state != "ON":
        st.error("⚠️ **SAFETY WARNING:** Heater is ON but pump is OFF! This is dangerous.")


def render_pump_control(mqtt_client: MQTTClient):
    """Render pump control panel."""
    st.subheader("💧 Pump Control")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Manual Control")
        pump_col1, pump_col2 = st.columns(2)

        with pump_col1:
            if st.button("✅ Turn ON", key="pump_on", width="stretch"):
                mqtt_client.set_pump_state("ON")
                st.success("Pump ON command sent")

        with pump_col2:
            if st.button("⛔ Turn OFF", key="pump_off", width="stretch"):
                mqtt_client.set_pump_state("OFF")
                st.success("Pump OFF command sent")

    with col2:
        st.markdown("##### Timed Run")
        timer_duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=480,
            value=30,
            step=5,
            key="pump_timer_duration",
        )

        timer_col1, timer_col2 = st.columns(2)

        with timer_col1:
            if st.button("⏱️ Start Timer", key="pump_timer_start", width="stretch"):
                mqtt_client.set_pump_timer(timer_duration)
                st.success(f"Pump timer started: {timer_duration} minutes")

        with timer_col2:
            if st.button("🛑 Cancel Timer", key="pump_timer_cancel", width="stretch"):
                mqtt_client.set_pump_timer(None)
                st.success("Pump timer cancelled")


def render_heater_control(mqtt_client: MQTTClient):
    """Render heater control panel."""
    st.subheader("🔥 Heater Control")

    sensor_data = mqtt_client.get_sensor_data()
    pump_state = sensor_data.get("pump_state", "UNKNOWN")

    # Safety check
    if pump_state != "ON":
        st.warning("⚠️ Pump must be ON before operating heater (safety feature)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Manual Control")
        heater_col1, heater_col2 = st.columns(2)

        with heater_col1:
            heater_on_disabled = pump_state != "ON"
            if st.button(
                "✅ Turn ON",
                key="heater_on",
                width="stretch",
                disabled=heater_on_disabled,
            ):
                mqtt_client.set_heater_state("ON")
                st.success("Heater ON command sent")

        with heater_col2:
            if st.button("⛔ Turn OFF", key="heater_off", width="stretch"):
                mqtt_client.set_heater_state("OFF")
                st.success("Heater OFF command sent")

    with col2:
        st.markdown("##### Heat to Target")
        target_temp = st.number_input(
            "Target Temperature (°C)",
            min_value=20.0,
            max_value=40.0,
            value=28.0,
            step=0.5,
            key="heater_target_temp",
        )

        if target_temp > 35.0:
            st.warning("⚠️ High temperature warning: >35°C may be unsafe")

        target_col1, target_col2 = st.columns(2)

        with target_col1:
            target_disabled = pump_state != "ON"
            if st.button(
                "🎯 Start Heating",
                key="heater_target_start",
                width="stretch",
                disabled=target_disabled,
            ):
                mqtt_client.set_heater_target(target_temp)
                st.success(f"Heater target set: {target_temp}°C")

        with target_col2:
            if st.button("🛑 Cancel Target", key="heater_target_cancel", width="stretch"):
                mqtt_client.set_heater_target(None)
                st.success("Heater target cancelled")


def render_light_control(mqtt_client: MQTTClient):
    """Render light control panel."""
    st.subheader("💡 Light Control")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Power Control")
        light_col1, light_col2 = st.columns(2)

        with light_col1:
            if st.button("✅ Turn ON", key="light_on", width="stretch"):
                mqtt_client.set_light_state("ON")
                st.success("Light ON command sent")

        with light_col2:
            if st.button("⛔ Turn OFF", key="light_off", width="stretch"):
                mqtt_client.set_light_state("OFF")
                st.success("Light OFF command sent")

    with col2:
        st.markdown("##### Color/Show Selection")
        selected_color = st.selectbox(
            "Select color or show",
            options=list(LIGHT_COLORS.keys()),
            format_func=lambda x: f"{x}: {LIGHT_COLORS[x]}",
            key="light_color_select",
        )

        # Color preview
        preview_color = LIGHT_COLOR_HEX.get(selected_color, "#FFFFFF")
        st.markdown(
            f"<div style='background-color:{preview_color}; height:30px; border-radius:5px; "
            f"border:1px solid #444;'></div>",
            unsafe_allow_html=True,
        )

        if st.button("🎨 Set Color", key="light_color_set", width="stretch"):
            mqtt_client.set_light_color(selected_color)
            st.success(f"Light color set: {LIGHT_COLORS[selected_color]}")


def render_temperature_history(mqtt_client: MQTTClient):
    """Render temperature history graph."""
    st.subheader("📈 Temperature History")

    sensor_history = mqtt_client.get_sensor_history()

    if len(sensor_history) < 2:
        st.info("Collecting sensor data... (need at least 2 data points)")
        return

    # Convert to DataFrame
    df = pd.DataFrame(sensor_history)

    # Create Plotly figure
    fig = go.Figure()

    # Add traces for each temperature sensor
    if "temp_sensor_in" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["temp_sensor_in"],
                mode="lines",
                name="Water Intake",
                line=dict(color="#00BCD4", width=2),
            )
        )

    if "temp_sensor_out" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["temp_sensor_out"],
                mode="lines",
                name="Water Output",
                line=dict(color="#FF6B6B", width=2),
            )
        )

    if "temp_ambient" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["temp_ambient"],
                mode="lines",
                name="Ambient",
                line=dict(color="#4CAF50", width=2),
            )
        )

    if "rpi_cpu_temp" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["rpi_cpu_temp"],
                mode="lines",
                name="RPi CPU",
                line=dict(color="#FFA726", width=2, dash="dash"),
            )
        )

    # Update layout
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        template="plotly_dark",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, width="stretch")


def render_mqtt_log(mqtt_client: MQTTClient):
    """Render MQTT message activity log."""
    with st.expander("📜 MQTT Activity Log", expanded=False):
        mqtt_log = mqtt_client.get_mqtt_log()

        if not mqtt_log:
            st.info("No MQTT messages logged yet")
            return

        # Display last 20 messages in reverse chronological order
        for msg in reversed(mqtt_log[-20:]):
            timestamp = msg["timestamp"].strftime("%H:%M:%S.%f")[:-3]
            topic = msg["topic"]
            payload = msg["payload"]

            # Truncate long payloads
            if len(payload) > 100:
                payload = payload[:100] + "..."

            st.text(f"[{timestamp}] {topic}: {payload}")


def main():
    """Main application entry point."""
    initialize_session_state()

    # Get MQTT client
    mqtt_client = get_mqtt_client()

    # Render UI
    render_header(mqtt_client)

    # Sensor dashboard
    render_sensor_dashboard(mqtt_client)

    st.divider()

    # Device status
    render_device_status(mqtt_client)

    st.divider()

    # Control panels in tabs
    tab1, tab2, tab3 = st.tabs(["💧 Pump", "🔥 Heater", "💡 Light"])

    with tab1:
        render_pump_control(mqtt_client)

    with tab2:
        render_heater_control(mqtt_client)

    with tab3:
        render_light_control(mqtt_client)

    st.divider()

    # Temperature history
    render_temperature_history(mqtt_client)

    st.divider()

    # MQTT log
    render_mqtt_log(mqtt_client)

    # Auto-refresh every 2 seconds
    st.session_state.last_refresh = datetime.now()
    import time

    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
