"""Tests for heater maximum runtime limit.

This module tests that the heater automatically shuts off after running
for a configurable maximum time to prevent runaway heating scenarios.

SAFETY REQUIREMENT:
The heater must not run indefinitely. A maximum runtime limit prevents:
- Equipment damage from continuous heating
- Energy waste from forgotten heater
- Overheating in case of sensor failure
- Environmental hazards from unattended heating
"""

import pytest
import logging
from unittest.mock import Mock, patch
import threading


@pytest.mark.safety
class TestHeaterMaxRuntime:
    """Tests for heater maximum runtime limit."""

    @pytest.fixture(autouse=True)
    def mock_event_and_db(self):
        """Auto-mock Event and DB for all tests in this class."""
        with patch('Event.Event.logStateEvent'), \
             patch('Event.Event.logOpaqueEvent') as mock_log_opaque, \
             patch('DB.DB.getInstance') as mock_db_get:

            mock_db = Mock()
            mock_db.logDuration = Mock()
            mock_db_get.return_value = mock_db
            self.mock_log_opaque = mock_log_opaque

            yield

    @pytest.fixture
    def mock_relay_block(self):
        """Mock relay block for heater tests."""
        relay = Mock()
        relay.portOn = Mock()
        relay.portOff = Mock()
        return relay

    @pytest.fixture
    def mock_pump(self):
        """Mock pump that is ON by default."""
        pump = Mock()
        pump.isOn = Mock(return_value=True)
        pump._state_lock = threading.RLock()
        return pump

    @pytest.fixture
    def heater_short_runtime(self, mock_relay_block, mock_pump):
        """Create Heater with short max runtime for testing (60 seconds)."""
        from Heater import Heater

        heater = Heater(
            relayBlock=mock_relay_block,
            heaterPort=7,
            maxWaterTemp=33,
            pump=mock_pump,
            maxRuntimeSeconds=60  # 1 minute for fast testing
        )
        return heater

    @pytest.fixture
    def heater_default_runtime(self, mock_relay_block, mock_pump):
        """Create Heater with default max runtime (4 hours)."""
        from Heater import Heater

        heater = Heater(
            relayBlock=mock_relay_block,
            heaterPort=7,
            maxWaterTemp=33,
            pump=mock_pump
            # No maxRuntimeSeconds - uses default
        )
        return heater

    def test_heater_has_max_runtime_attribute(self, heater_short_runtime):
        """Verify heater has maxRuntimeSeconds attribute."""
        assert hasattr(heater_short_runtime, 'maxRuntimeSeconds')
        assert heater_short_runtime.maxRuntimeSeconds == 60

    def test_heater_default_max_runtime(self, heater_default_runtime):
        """Verify heater defaults to 4 hours max runtime."""
        # Default is 4 hours = 14400 seconds
        assert heater_default_runtime.maxRuntimeSeconds == 4 * 3600

    def test_heater_stops_after_max_runtime(self, heater_short_runtime, caplog):
        """SAFETY: Heater must stop after exceeding max runtime."""
        heater = heater_short_runtime

        # Start heater
        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()
        assert heater.isOn() is True

        # Simulate timer showing exceeded runtime
        with patch.object(heater.timer, 'elapsedSeconds', return_value=61):  # > 60 seconds
            with caplog.at_level(logging.ERROR):
                heater.runOneLoop()

        # Verify heater stopped
        assert heater.isOn() is False, "Heater should stop after max runtime exceeded"
        assert "Maximum runtime" in caplog.text
        assert "exceeded" in caplog.text

    def test_heater_logs_runtime_exceeded_event(self, heater_short_runtime):
        """Verify heater logs event when runtime exceeded."""
        heater = heater_short_runtime

        heater.setInputTemp(25.0)
        heater.on()

        with patch.object(heater.timer, 'elapsedSeconds', return_value=120):  # 2x limit
            heater.runOneLoop()

        # Verify event logged
        self.mock_log_opaque.assert_called()
        calls = [str(c) for c in self.mock_log_opaque.call_args_list]
        assert any('heater_max_runtime_exceeded' in c for c in calls)

    def test_heater_runs_within_limit(self, heater_short_runtime, caplog):
        """Verify heater continues running within time limit."""
        heater = heater_short_runtime

        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()

        # Simulate timer showing within limit
        with patch.object(heater.timer, 'elapsedSeconds', return_value=30):  # 30 < 60 seconds
            heater.runOneLoop()

        # Verify heater still running
        assert heater.isOn() is True, "Heater should continue within time limit"

    def test_heater_exactly_at_limit(self, heater_short_runtime):
        """Verify heater behavior at exactly the time limit."""
        heater = heater_short_runtime

        heater.setInputTemp(25.0)
        heater.setModeHoldTemp(30)
        heater.on()

        # Exactly at limit - should still run (limit is exceeded, not reached)
        with patch.object(heater.timer, 'elapsedSeconds', return_value=60):  # == 60 seconds
            heater.runOneLoop()

        # At exactly the limit, should still run (> not >=)
        assert heater.isOn() is True, "Heater should run at exactly the limit"

        # One second over - should stop
        with patch.object(heater.timer, 'elapsedSeconds', return_value=61):  # > 60 seconds
            heater.runOneLoop()

        assert heater.isOn() is False, "Heater should stop when limit exceeded"

    def test_heater_runtime_check_only_when_on(self, heater_short_runtime):
        """Verify runtime check only applies when heater is ON."""
        heater = heater_short_runtime

        # Heater is OFF
        assert heater.isOn() is False

        # Even with "exceeded" timer, OFF heater shouldn't trigger error
        with patch.object(heater.timer, 'elapsedSeconds', return_value=1000):
            heater.runOneLoop()

        # Should still be OFF (no error, just normal behavior)
        assert heater.isOn() is False


@pytest.mark.unit
class TestHeaterRuntimeConfiguration:
    """Tests for runtime configuration from config file."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons for isolated tests."""
        from Config import Config
        Config._Config__instance = None
        yield
        Config._Config__instance = None

    def test_config_reads_max_runtime(self, test_config_file, monkeypatch):
        """Verify Config reads maxHeaterRuntimeSeconds."""
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        assert hasattr(config, 'maxHeaterRuntimeSeconds')
        assert config.maxHeaterRuntimeSeconds == 14400  # 4 hours from test config

    def test_config_defaults_max_runtime(self, tmp_path, monkeypatch):
        """Verify Config uses default if maxHeaterRuntimeSeconds not in config."""
        import json
        from Config import Config

        # Create config WITHOUT maxHeaterRuntimeSeconds
        minimal_config = {
            "tempSensors": {
                "in_to_heater": {"name": "test", "device": "/dev/null"},
                "out_from_heater": {"name": "test", "device": "/dev/null"},
                "temp_ambient": {"name": "test", "device": "/dev/null"}
            },
            "pumpPort": 8,
            "heaterPort": 7,
            "lightPort": 6,
            "pumpSpeedS1Port": 1,
            "pumpSpeedS2Port": 2,
            "pumpSpeedS3Port": 3,
            "pumpSpeedS4Port": 4,
            "maxWaterTemp": 33,
            "pingTarget": "127.0.0.1",
            # NO maxHeaterRuntimeSeconds
            "dbName": "test",
            "dbUser": "test",
            "dbPassword": "test"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(minimal_config, f)

        monkeypatch.chdir(tmp_path)
        config = Config()

        # Should default to 4 hours
        assert config.maxHeaterRuntimeSeconds == 4 * 3600

    def test_config_json_has_max_runtime_field(self):
        """Verify config.json includes maxHeaterRuntimeSeconds."""
        import json
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config.json"

        assert config_file.exists()

        with open(config_file) as f:
            config_data = json.load(f)

        assert "maxHeaterRuntimeSeconds" in config_data
        assert config_data["maxHeaterRuntimeSeconds"] == 14400  # 4 hours
