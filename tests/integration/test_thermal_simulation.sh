#!/bin/bash
# Test script to verify thermal simulation physics

echo "=== Testing Thermal Simulation ==="
echo ""
echo "Starting PiPool in simulated mode..."
echo "This script will:"
echo "1. Start the system (heater and pump OFF)"
echo "2. Turn on the pump (heater still OFF - temps should stay same)"
echo "3. Turn on the heater (temps should rise)"
echo "4. Turn off the heater (temps should return to pool temp)"
echo ""

# Start pipool in background
PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py &
PIPOOL_PID=$!

# Wait for startup
sleep 5

echo "=== Phase 1: Baseline (Pump OFF, Heater OFF) ==="
mosquitto_sub -h localhost -t "pipool/sensors" -C 1 | jq '.temp_sensor_in, .temp_sensor_out'

echo ""
echo "=== Phase 2: Turn ON pump (Heater still OFF) ==="
mosquitto_pub -h localhost -t "pipool/control/pump_state" -m "ON"
sleep 3
mosquitto_sub -h localhost -t "pipool/sensors" -C 1 | jq '.temp_sensor_in, .temp_sensor_out'

echo ""
echo "=== Phase 3: Turn ON heater (should see +10C rise in output temp) ==="
mosquitto_pub -h localhost -t "pipool/control/heater_state" -m "ON"
sleep 3
mosquitto_sub -h localhost -t "pipool/sensors" -C 1 | jq '.temp_sensor_in, .temp_sensor_out'

echo ""
echo "=== Phase 4: Wait 5 seconds (pool should start warming) ==="
sleep 5
mosquitto_sub -h localhost -t "pipool/sensors" -C 1 | jq '.temp_sensor_in, .temp_sensor_out'

echo ""
echo "=== Phase 5: Turn OFF heater (output should return to pool temp) ==="
mosquitto_pub -h localhost -t "pipool/control/heater_state" -m "OFF"
sleep 3
mosquitto_sub -h localhost -t "pipool/sensors" -C 1 | jq '.temp_sensor_in, .temp_sensor_out'

echo ""
echo "=== Test complete! Shutting down PiPool ==="
kill $PIPOOL_PID
wait $PIPOOL_PID 2>/dev/null

echo ""
echo "Expected behavior:"
echo "- Phase 1: in ≈ 26C, out ≈ 26C (both at pool temp)"
echo "- Phase 2: in ≈ 26C, out ≈ 26C (pump on, heater off)"
echo "- Phase 3: in ≈ 26C, out ≈ 36C (heater adds 10C)"
echo "- Phase 4: in ≈ 26.x C, out ≈ 36.x C (pool warming slowly)"
echo "- Phase 5: in ≈ 26.x C, out ≈ 26.x C (heater off, both at pool temp)"
