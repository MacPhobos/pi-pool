#!/bin/bash
# Verify PiPool Streamlit Dashboard installation

echo "=============================================="
echo "PiPool Dashboard - Installation Verification"
echo "=============================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ $python_version"
else
    echo "   ❌ Python 3 not found"
    exit 1
fi
echo ""

# Check pip
echo "2. Checking pip..."
pip_version=$(pip3 --version 2>&1 | head -n1)
if [ $? -eq 0 ]; then
    echo "   ✅ $pip_version"
else
    echo "   ❌ pip not found"
    exit 1
fi
echo ""

# Check required Python packages
echo "3. Checking required packages..."

packages=("streamlit" "paho.mqtt" "pandas" "plotly")
all_installed=true

for package in "${packages[@]}"; do
    if python3 -c "import ${package//./_}" 2>/dev/null; then
        version=$(python3 -c "import ${package//./_}; print(${package//./_}.__version__)" 2>/dev/null)
        echo "   ✅ ${package} (${version})"
    else
        echo "   ❌ ${package} not installed"
        all_installed=false
    fi
done
echo ""

if [ "$all_installed" = false ]; then
    echo "⚠️  Missing packages detected!"
    echo ""
    echo "Install with:"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Or with uv:"
    echo "  uv pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Check file structure
echo "4. Checking file structure..."
files=("app.py" "mqtt_client.py" "requirements.txt" ".streamlit/config.toml")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file missing"
        exit 1
    fi
done
echo ""

# Check MQTT connectivity
echo "5. Checking MQTT broker connectivity..."
broker_host=${MQTT_BROKER_HOST:-192.168.1.23}
broker_port=${MQTT_BROKER_PORT:-1883}

echo "   Broker: ${broker_host}:${broker_port}"

# Try to ping the broker (requires nc - netcat)
if command -v nc &> /dev/null; then
    if nc -z -w 2 "$broker_host" "$broker_port" 2>/dev/null; then
        echo "   ✅ MQTT broker reachable at ${broker_host}:${broker_port}"
    else
        echo "   ⚠️  Cannot reach MQTT broker at ${broker_host}:${broker_port}"
        echo "      This is OK if broker is not running yet"
    fi
else
    if command -v ping &> /dev/null; then
        if ping -c 1 -W 2 "$broker_host" &>/dev/null; then
            echo "   ✅ Host ${broker_host} is reachable (port check skipped, nc not available)"
        else
            echo "   ⚠️  Cannot reach host ${broker_host}"
            echo "      This is OK if broker is not running yet"
        fi
    else
        echo "   ⚠️  Cannot check connectivity (nc and ping not available)"
    fi
fi
echo ""

# Summary
echo "=============================================="
echo "✅ Installation verification complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Start the dashboard:"
echo "     ./run_streamlit.sh"
echo ""
echo "  2. Test MQTT connection (optional):"
echo "     python test_mqtt_connection.py"
echo ""
echo "  3. Access the dashboard:"
echo "     http://localhost:8501"
echo ""
echo "=============================================="
