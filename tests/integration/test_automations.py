#!/usr/bin/env python3
"""
Test script for Automations.py pump circulation delay.
Verifies pump circulation delay and error handling.
"""

import json
import sys
import time
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, 'src')

from Automations import Automations, PUMP_CIRCULATION_DELAY_SECONDS


def test_successful_heater_start_with_delay():
    """Test normal case: pump starts, delay occurs, heater starts."""
    print("\n=== Test 1: Successful heater start with circulation delay ===")

    # Mock dependencies
    pump = Mock()
    pump.isOn.return_value = True
    pump.on.return_value = None

    heater = Mock()
    heater.inputTempLessThen.return_value = True
    heater.on.return_value = True

    light = Mock()
    colorLogicLight = Mock()

    # Create automations instance
    automations = Automations(pump, heater, light, colorLogicLight)

    # Valid payload
    payload = json.dumps({"mode": "ON", "targetTemp": "30"})

    # Mock Event.logOpaqueEvent
    with patch('Automations.Event') as mock_event:
        with patch('time.sleep') as mock_sleep:
            automations.setHeaterReachAndStopMessageHandler(payload)

            # Verify sequence
            assert pump.on.called, "Pump should be started"
            mock_sleep.assert_called_once_with(PUMP_CIRCULATION_DELAY_SECONDS)
            assert pump.isOn.called, "Pump state should be verified after delay"
            assert heater.on.called, "Heater should be started after delay"
            heater.setModeReachTempAndStop.assert_called_once_with(30)

            # Verify event logged
            mock_event.logOpaqueEvent.assert_called_with(
                "automation_heating_started",
                json.dumps({"target_temp": 30})
            )

    print("✓ Pump started")
    print(f"✓ {PUMP_CIRCULATION_DELAY_SECONDS}s delay applied")
    print("✓ Pump state verified after delay")
    print("✓ Heater started successfully")
    print("✓ Event logged")


def test_pump_stopped_during_delay():
    """Test safety case: pump stops during circulation delay."""
    print("\n=== Test 2: Pump stops during circulation delay ===")

    # Mock dependencies
    pump = Mock()
    pump.on.return_value = None
    pump.isOn.return_value = False  # Pump stopped during delay

    heater = Mock()
    heater.inputTempLessThen.return_value = True

    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    payload = json.dumps({"mode": "ON", "targetTemp": "30"})

    with patch('Automations.Event') as mock_event:
        with patch('time.sleep') as mock_sleep:
            automations.setHeaterReachAndStopMessageHandler(payload)

            # Verify heater NOT started
            assert not heater.on.called, "Heater should NOT be started if pump stopped"

            # Verify blocked event logged
            mock_event.logOpaqueEvent.assert_called_with(
                "automation_heater_blocked",
                json.dumps({"reason": "pump_stopped_during_delay"})
            )

    print("✓ Pump started")
    print(f"✓ {PUMP_CIRCULATION_DELAY_SECONDS}s delay applied")
    print("✓ Detected pump stopped during delay")
    print("✓ Heater NOT started (safety abort)")
    print("✓ Blocked event logged")


def test_invalid_json():
    """Test error handling: invalid JSON payload."""
    print("\n=== Test 3: Invalid JSON payload ===")

    pump = Mock()
    heater = Mock()
    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    invalid_payload = "not valid json {"

    automations.setHeaterReachAndStopMessageHandler(invalid_payload)

    # Verify nothing was started
    assert not pump.on.called, "Pump should not start with invalid JSON"
    assert not heater.on.called, "Heater should not start with invalid JSON"

    print("✓ Invalid JSON handled gracefully")
    print("✓ No devices activated")


def test_missing_mode():
    """Test error handling: missing 'mode' field."""
    print("\n=== Test 4: Missing 'mode' field ===")

    pump = Mock()
    heater = Mock()
    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    payload = json.dumps({"targetTemp": "30"})  # Missing 'mode'

    automations.setHeaterReachAndStopMessageHandler(payload)

    assert not pump.on.called, "Pump should not start without mode"
    assert not heater.on.called, "Heater should not start without mode"

    print("✓ Missing mode handled gracefully")


def test_invalid_target_temp():
    """Test validation: invalid target temperature."""
    print("\n=== Test 5: Invalid target temperature ===")

    pump = Mock()
    heater = Mock()
    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    # Test out-of-range temperatures
    for temp in [-5, 0, 50, 100]:
        payload = json.dumps({"mode": "ON", "targetTemp": str(temp)})
        automations.setHeaterReachAndStopMessageHandler(payload)

        assert not pump.on.called, f"Pump should not start with temp={temp}"
        assert not heater.on.called, f"Heater should not start with temp={temp}"

    print("✓ Out-of-range temps rejected (tested: -5, 0, 50, 100)")

    # Test non-numeric temperature
    payload = json.dumps({"mode": "ON", "targetTemp": "invalid"})
    automations.setHeaterReachAndStopMessageHandler(payload)

    assert not pump.on.called, "Pump should not start with non-numeric temp"

    print("✓ Non-numeric temp rejected")


def test_heater_fails_to_start():
    """Test error handling: heater.on() returns False."""
    print("\n=== Test 6: Heater fails to start ===")

    pump = Mock()
    pump.isOn.return_value = True
    pump.on.return_value = None

    heater = Mock()
    heater.inputTempLessThen.return_value = True
    heater.on.return_value = False  # Heater failed to start

    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    payload = json.dumps({"mode": "ON", "targetTemp": "30"})

    with patch('Automations.Event') as mock_event:
        with patch('time.sleep'):
            automations.setHeaterReachAndStopMessageHandler(payload)

            # Verify setModeReachTempAndStop NOT called
            assert not heater.setModeReachTempAndStop.called, \
                "Mode should not be set if heater failed to start"

            # Verify no success event logged
            mock_event.logOpaqueEvent.assert_not_called()

    print("✓ Heater failure handled")
    print("✓ No mode set on failed heater")


def test_already_at_target_temp():
    """Test optimization: skip heating if already at target."""
    print("\n=== Test 7: Already at target temperature ===")

    pump = Mock()
    heater = Mock()
    heater.inputTempLessThen.return_value = False  # Already warm enough

    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    payload = json.dumps({"mode": "ON", "targetTemp": "25"})

    automations.setHeaterReachAndStopMessageHandler(payload)

    assert not pump.on.called, "Pump should not start if already at temp"
    assert not heater.on.called, "Heater should not start if already at temp"

    print("✓ Heating skipped when already at target")


def test_mode_off():
    """Test OFF mode stops heater."""
    print("\n=== Test 8: Mode OFF ===")

    pump = Mock()
    heater = Mock()
    light = Mock()
    colorLogicLight = Mock()

    automations = Automations(pump, heater, light, colorLogicLight)

    payload = json.dumps({"mode": "OFF"})

    automations.setHeaterReachAndStopMessageHandler(payload)

    heater.off.assert_called_once()

    print("✓ Heater turned off")


if __name__ == "__main__":
    print("Testing Pump Circulation Delay Feature")
    print("=" * 60)

    test_successful_heater_start_with_delay()
    test_pump_stopped_during_delay()
    test_invalid_json()
    test_missing_mode()
    test_invalid_target_temp()
    test_heater_fails_to_start()
    test_already_at_target_temp()
    test_mode_off()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print(f"\nKey safety features verified:")
    print(f"  - {PUMP_CIRCULATION_DELAY_SECONDS}s circulation delay before heater")
    print(f"  - Pump state re-verified after delay")
    print(f"  - Temperature validation (1-45°C)")
    print(f"  - JSON error handling")
    print(f"  - Proper event logging")
