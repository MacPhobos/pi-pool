"""Unit tests for mode enums.

Tests PumpMode and HeaterMode enumerations.
"""

import pytest
from PumpMode import PumpMode
from HeaterMode import HeaterMode


@pytest.mark.unit
class TestPumpMode:
    """Unit tests for PumpMode enum."""

    def test_pump_mode_off(self):
        """PumpMode.OFF should have value 'OFF'."""
        assert PumpMode.OFF.value == "OFF"

    def test_pump_mode_hold(self):
        """PumpMode.HOLD should have value 'HOLD'."""
        assert PumpMode.HOLD.value == "HOLD"

    def test_pump_mode_reach_time_and_stop(self):
        """PumpMode.REACH_TIME_AND_STOP should have value 'REACH_TIME_AND_STOP'."""
        assert PumpMode.REACH_TIME_AND_STOP.value == "REACH_TIME_AND_STOP"

    def test_pump_mode_enum_members(self):
        """PumpMode should have exactly three members."""
        assert len(list(PumpMode)) == 3
        assert PumpMode.OFF in PumpMode
        assert PumpMode.HOLD in PumpMode
        assert PumpMode.REACH_TIME_AND_STOP in PumpMode

    def test_pump_mode_string_representation(self):
        """PumpMode members should have correct string representation."""
        assert str(PumpMode.OFF) == "PumpMode.OFF"
        assert str(PumpMode.HOLD) == "PumpMode.HOLD"
        assert str(PumpMode.REACH_TIME_AND_STOP) == "PumpMode.REACH_TIME_AND_STOP"

    def test_pump_mode_equality(self):
        """PumpMode members should be comparable."""
        assert PumpMode.OFF == PumpMode.OFF
        assert PumpMode.HOLD == PumpMode.HOLD
        assert PumpMode.OFF != PumpMode.HOLD


@pytest.mark.unit
class TestHeaterMode:
    """Unit tests for HeaterMode enum."""

    def test_heater_mode_off(self):
        """HeaterMode.OFF should have value 'OFF'."""
        assert HeaterMode.OFF.value == "OFF"

    def test_heater_mode_hold(self):
        """HeaterMode.HOLD should have value 'HOLD'."""
        assert HeaterMode.HOLD.value == "HOLD"

    def test_heater_mode_reach_and_stop(self):
        """HeaterMode.REACH_AND_STOP should have value 'REACH_AND_STOP'."""
        assert HeaterMode.REACH_AND_STOP.value == "REACH_AND_STOP"

    def test_heater_mode_enum_members(self):
        """HeaterMode should have exactly three members."""
        assert len(list(HeaterMode)) == 3
        assert HeaterMode.OFF in HeaterMode
        assert HeaterMode.HOLD in HeaterMode
        assert HeaterMode.REACH_AND_STOP in HeaterMode

    def test_heater_mode_string_representation(self):
        """HeaterMode members should have correct string representation."""
        assert str(HeaterMode.OFF) == "HeaterMode.OFF"
        assert str(HeaterMode.HOLD) == "HeaterMode.HOLD"
        assert str(HeaterMode.REACH_AND_STOP) == "HeaterMode.REACH_AND_STOP"

    def test_heater_mode_equality(self):
        """HeaterMode members should be comparable."""
        assert HeaterMode.OFF == HeaterMode.OFF
        assert HeaterMode.HOLD == HeaterMode.HOLD
        assert HeaterMode.REACH_AND_STOP == HeaterMode.REACH_AND_STOP
        assert HeaterMode.OFF != HeaterMode.HOLD

    def test_heater_mode_in_conditional(self):
        """HeaterMode should work correctly in conditional expressions."""
        mode = HeaterMode.HOLD
        assert mode == HeaterMode.HOLD

        mode = HeaterMode.OFF
        assert mode == HeaterMode.OFF
