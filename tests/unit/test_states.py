"""Unit tests for state enums.

Tests PumpState, HeaterState, and LightState enumerations.
"""

import pytest
from PumpState import PumpState
from HeaterState import HeaterState
from LightState import LightState


@pytest.mark.unit
class TestPumpState:
    """Unit tests for PumpState enum."""

    def test_pump_state_on(self):
        """PumpState.ON should have value 'ON'."""
        assert PumpState.ON.value == "ON"

    def test_pump_state_off(self):
        """PumpState.OFF should have value 'OFF'."""
        assert PumpState.OFF.value == "OFF"

    def test_pump_state_reach_and_stop(self):
        """PumpState.REACH_AND_STOP should have value 'REACH_AND_STOP'."""
        assert PumpState.REACH_AND_STOP.value == "REACH_AND_STOP"

    def test_pump_state_enum_members(self):
        """PumpState should have exactly three members."""
        assert len(list(PumpState)) == 3
        assert PumpState.ON in PumpState
        assert PumpState.OFF in PumpState
        assert PumpState.REACH_AND_STOP in PumpState

    def test_pump_state_string_representation(self):
        """PumpState members should have correct string representation."""
        assert str(PumpState.ON) == "PumpState.ON"
        assert str(PumpState.OFF) == "PumpState.OFF"


@pytest.mark.unit
class TestHeaterState:
    """Unit tests for HeaterState enum."""

    def test_heater_state_on(self):
        """HeaterState.ON should have value 'ON'."""
        assert HeaterState.ON.value == "ON"

    def test_heater_state_off(self):
        """HeaterState.OFF should have value 'OFF'."""
        assert HeaterState.OFF.value == "OFF"

    def test_heater_state_enum_members(self):
        """HeaterState should have exactly two members."""
        assert len(list(HeaterState)) == 2
        assert HeaterState.ON in HeaterState
        assert HeaterState.OFF in HeaterState

    def test_heater_state_string_representation(self):
        """HeaterState members should have correct string representation."""
        assert str(HeaterState.ON) == "HeaterState.ON"
        assert str(HeaterState.OFF) == "HeaterState.OFF"

    def test_heater_state_equality(self):
        """HeaterState members should be comparable."""
        assert HeaterState.ON == HeaterState.ON
        assert HeaterState.OFF == HeaterState.OFF
        assert HeaterState.ON != HeaterState.OFF


@pytest.mark.unit
class TestLightState:
    """Unit tests for LightState enum."""

    def test_light_state_on(self):
        """LightState.ON should have value 'ON'."""
        assert LightState.ON.value == "ON"

    def test_light_state_off(self):
        """LightState.OFF should have value 'OFF'."""
        assert LightState.OFF.value == "OFF"

    def test_light_state_enum_members(self):
        """LightState should have exactly two members."""
        assert len(list(LightState)) == 2
        assert LightState.ON in LightState
        assert LightState.OFF in LightState

    def test_light_state_string_representation(self):
        """LightState members should have correct string representation."""
        assert str(LightState.ON) == "LightState.ON"
        assert str(LightState.OFF) == "LightState.OFF"

    def test_light_state_equality(self):
        """LightState members should be comparable."""
        assert LightState.ON == LightState.ON
        assert LightState.OFF == LightState.OFF
        assert LightState.ON != LightState.OFF

    def test_light_state_in_conditional(self):
        """LightState should work correctly in conditional expressions."""
        state = LightState.ON
        assert state == LightState.ON

        state = LightState.OFF
        assert state == LightState.OFF
