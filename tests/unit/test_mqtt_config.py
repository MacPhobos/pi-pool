"""Tests for MQTT broker configuration.

This module tests that the MQTT broker address is properly read from
configuration instead of being hardcoded.

REQUIREMENT:
The MQTT broker address must be configurable via config.json to allow
deployment in different network environments without code changes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestMqttBrokerConfiguration:
    """Tests for configurable MQTT broker address."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons for isolated tests."""
        from Config import Config
        Config._Config__instance = None
        yield
        Config._Config__instance = None

    def test_config_reads_mqtt_broker(self, test_config_file, monkeypatch):
        """Verify Config reads mqttBroker from config file."""
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        # Should have mqttBroker from test config
        assert hasattr(config, 'mqttBroker'), "Config should have mqttBroker attribute"
        assert config.mqttBroker == "127.0.0.1", "mqttBroker should be read from config"

    def test_config_defaults_mqtt_broker_if_missing(self, tmp_path, monkeypatch):
        """Verify Config uses default if mqttBroker not in config."""
        import json
        from Config import Config

        # Create config WITHOUT mqttBroker
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
            # NO mqttBroker key
            "dbName": "test",
            "dbUser": "test",
            "dbPassword": "test"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(minimal_config, f)

        monkeypatch.chdir(tmp_path)
        config = Config()

        # Should default to 192.168.1.23 for backward compatibility
        assert config.mqttBroker == "192.168.1.23", "Should default for backward compatibility"

    def test_message_bus_uses_configured_broker(self, test_config_file, monkeypatch):
        """Verify MessageBus uses broker from Config."""
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        # Create mock MQTT client
        mock_mqtt_client = Mock()
        mock_mqtt_client.connect = Mock()

        with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
            from MessageBus import MessageBus

            # Create MessageBus (should get broker from Config)
            bus = MessageBus(
                pump=Mock(),
                light=Mock(),
                heater=Mock(),
                lightColorLogic=Mock()
            )

            # Verify broker address from config
            assert bus.mqttBroker == "127.0.0.1", "MessageBus should use broker from config"

    def test_message_bus_accepts_explicit_broker(self, test_config_file, monkeypatch):
        """Verify MessageBus can accept explicit broker address."""
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        mock_mqtt_client = Mock()

        with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
            from MessageBus import MessageBus

            # Create MessageBus with explicit broker
            bus = MessageBus(
                pump=Mock(),
                light=Mock(),
                heater=Mock(),
                lightColorLogic=Mock(),
                mqttBroker="192.168.1.100"  # Explicit override
            )

            assert bus.mqttBroker == "192.168.1.100", "MessageBus should use explicit broker"

    def test_message_bus_connect_uses_configured_broker(self, test_config_file, monkeypatch, caplog):
        """Verify MessageBus.connect() uses the configured broker address."""
        import logging
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        mock_mqtt_client = Mock()
        mock_mqtt_client.connect = Mock()

        with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
            from MessageBus import MessageBus

            bus = MessageBus(
                pump=Mock(),
                light=Mock(),
                heater=Mock(),
                lightColorLogic=Mock(),
                mqttBroker="test.broker.local"
            )

            with caplog.at_level(logging.INFO):
                bus.connect()

            # Verify connect was called with configured broker
            mock_mqtt_client.connect.assert_called_once_with("test.broker.local")

            # Verify log message includes broker address
            assert "test.broker.local" in caplog.text

    def test_message_bus_connect_error_includes_broker(self, test_config_file, monkeypatch, caplog):
        """Verify connection errors include the broker address for debugging."""
        import logging
        from Config import Config

        monkeypatch.chdir(test_config_file.parent)
        config = Config()

        mock_mqtt_client = Mock()
        mock_mqtt_client.connect = Mock(side_effect=Exception("Connection refused"))

        with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
            from MessageBus import MessageBus

            bus = MessageBus(
                pump=Mock(),
                light=Mock(),
                heater=Mock(),
                lightColorLogic=Mock(),
                mqttBroker="bad.broker.local"
            )

            with caplog.at_level(logging.ERROR):
                bus.connect()

            # Verify error message includes broker address
            assert "bad.broker.local" in caplog.text
            assert "Connection refused" in caplog.text


@pytest.mark.unit
class TestMqttBrokerIntegration:
    """Integration tests for MQTT broker configuration."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self):
        """Reset singletons for isolated tests."""
        from Config import Config
        Config._Config__instance = None
        yield
        Config._Config__instance = None

    def test_config_json_has_mqtt_broker_field(self):
        """Verify config.json includes mqttBroker field."""
        import json
        from pathlib import Path

        # Find config.json in project root
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config.json"

        assert config_file.exists(), "config.json should exist in project root"

        with open(config_file) as f:
            config_data = json.load(f)

        assert "mqttBroker" in config_data, "config.json should have mqttBroker field"
        assert config_data["mqttBroker"], "mqttBroker should not be empty"
