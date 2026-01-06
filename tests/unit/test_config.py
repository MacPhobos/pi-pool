"""Unit tests for Config module.

Tests configuration loading, validation, and hardware mode detection.
"""

import pytest
import json
import os
from pathlib import Path


@pytest.mark.unit
def test_config_loads_from_file(config):
    """Test Config singleton loads configuration from JSON file."""
    assert config is not None
    assert config.pumpPort == 8
    assert config.heaterPort == 7
    assert config.lightPort == 6
    assert config.maxWaterTemp == 33


@pytest.mark.unit
def test_config_hardware_mode_simulated(config):
    """Test Config recognizes simulated hardware mode."""
    from hal import HardwareMode

    mode = config.getHardwareMode()
    assert mode == HardwareMode.SIMULATED


@pytest.mark.unit
def test_config_sensor_paths(config):
    """Test Config loads sensor paths correctly."""
    assert config.tempSensorIn is not None
    assert config.tempSensorOut is not None
    assert config.tempAmbient is not None

    assert 'name' in config.tempSensorIn
    assert 'device' in config.tempSensorIn


@pytest.mark.unit
def test_config_validates_gpio_ports(tmp_path, monkeypatch):
    """Test Config validates GPIO port numbers are in valid range."""
    from Config import Config

    # Create config with invalid port
    invalid_config = {
        "tempSensors": {
            "in_to_heater": {"name": "temp_in", "device": "/dev/null"},
            "out_from_heater": {"name": "temp_out", "device": "/dev/null"},
            "temp_ambient": {"name": "temp_ambient", "device": "/dev/null"}
        },
        "pumpPort": 99,  # Invalid port
        "heaterPort": 7,
        "lightPort": 6,
        "pumpSpeedS1Port": 1,
        "pumpSpeedS2Port": 2,
        "pumpSpeedS3Port": 3,
        "pumpSpeedS4Port": 4,
        "maxWaterTemp": 33,
        "pingTarget": "127.0.0.1",
        "dbName": "pipool_test",
        "dbUser": "pipool_test",
        "dbPassword": "pipool_test",
        "hardwareMode": "simulated"
    }

    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(invalid_config, f)

    monkeypatch.chdir(tmp_path)

    # Should raise ValueError for invalid port
    with pytest.raises(ValueError, match="Invalid pumpPort"):
        Config()


@pytest.mark.unit
def test_config_singleton_pattern(config):
    """Test Config implements singleton pattern correctly."""
    from Config import Config

    # getInstance should return same instance
    same_instance = Config.getInstance()
    assert same_instance is config


@pytest.mark.unit
def test_config_custom_overrides_default(tmp_path, monkeypatch):
    """Test config_custom.json overrides config.json."""
    from Config import Config

    # Create default config
    default_config = {
        "tempSensors": {
            "in_to_heater": {"name": "temp_in", "device": "/dev/null"},
            "out_from_heater": {"name": "temp_out", "device": "/dev/null"},
            "temp_ambient": {"name": "temp_ambient", "device": "/dev/null"}
        },
        "pumpPort": 8,
        "heaterPort": 7,
        "lightPort": 6,
        "pumpSpeedS1Port": 1,
        "pumpSpeedS2Port": 2,
        "pumpSpeedS3Port": 3,
        "pumpSpeedS4Port": 4,
        "maxWaterTemp": 30,  # Default temp
        "pingTarget": "127.0.0.1",
        "dbName": "pipool",
        "dbUser": "pipool",
        "dbPassword": "pipool",
        "hardwareMode": "simulated"
    }

    # Create custom config with override
    custom_config = default_config.copy()
    custom_config["maxWaterTemp"] = 35  # Override temp

    config_file = tmp_path / "config.json"
    custom_file = tmp_path / "config_custom.json"

    with open(config_file, 'w') as f:
        json.dump(default_config, f)

    with open(custom_file, 'w') as f:
        json.dump(custom_config, f)

    monkeypatch.chdir(tmp_path)

    # Reset singleton
    Config._Config__instance = None

    # Load config - should use custom
    loaded_config = Config()

    assert loaded_config.maxWaterTemp == 35  # Custom value, not default


@pytest.mark.unit
def test_config_environment_variable_hardware_mode(tmp_path, monkeypatch):
    """Test PIPOOL_HARDWARE_MODE environment variable overrides config."""
    from Config import Config
    from hal import HardwareMode

    # Create config with real mode
    test_config = {
        "tempSensors": {
            "in_to_heater": {"name": "temp_in", "device": "/dev/null"},
            "out_from_heater": {"name": "temp_out", "device": "/dev/null"},
            "temp_ambient": {"name": "temp_ambient", "device": "/dev/null"}
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
        "dbName": "pipool_test",
        "dbUser": "pipool_test",
        "dbPassword": "pipool_test",
        "hardwareMode": "real"  # Config says real
    }

    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(test_config, f)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PIPOOL_HARDWARE_MODE', 'simulated')  # Env says simulated

    # Reset singleton
    Config._Config__instance = None

    # Load config
    loaded_config = Config()

    # Environment variable should override config file
    assert loaded_config.getHardwareMode() == HardwareMode.SIMULATED
