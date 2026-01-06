"""Unit tests for Sensors collection class.

Tests the Sensors class that manages multiple sensor instances.
"""

import pytest
import json
from unittest.mock import Mock
from Sensors import Sensors
from Sensor import Sensor


@pytest.mark.unit
class TestSensors:
    """Unit tests for Sensors collection class."""

    @pytest.fixture
    def mock_sensor_device_1(self):
        """Provide first mock sensor device."""
        mock = Mock()
        mock.getName.return_value = "temp_sensor_1"
        mock.getCurrentReading.return_value = 25.5
        mock.status.return_value = {"temp_sensor_1": 25.5}
        return mock

    @pytest.fixture
    def mock_sensor_device_2(self):
        """Provide second mock sensor device."""
        mock = Mock()
        mock.getName.return_value = "temp_sensor_2"
        mock.getCurrentReading.return_value = 30.0
        mock.status.return_value = {"temp_sensor_2": 30.0}
        return mock

    @pytest.fixture
    def sensors_collection(self, mock_db_singleton):
        """Provide Sensors collection instance."""
        return Sensors()

    def test_sensors_initialization(self):
        """Sensors should initialize with empty list."""
        sensors = Sensors()

        assert sensors.sensors == []
        assert len(sensors.sensors) == 0

    def test_sensors_add_sensor(self, sensors_collection, mock_sensor_device_1, mock_db_singleton):
        """Sensors should allow adding sensor instances."""
        sensor = Sensor(mock_sensor_device_1)
        sensors_collection.addSensor(sensor)

        assert len(sensors_collection.sensors) == 1
        assert sensors_collection.sensors[0] == sensor

    def test_sensors_get_by_name(self, sensors_collection, mock_sensor_device_1, mock_sensor_device_2, mock_db_singleton):
        """Sensors should retrieve sensor by name."""
        sensor1 = Sensor(mock_sensor_device_1)
        sensor2 = Sensor(mock_sensor_device_2)

        sensors_collection.addSensor(sensor1)
        sensors_collection.addSensor(sensor2)

        found = sensors_collection.getSensor("temp_sensor_1")
        assert found == sensor1
        assert found.getName() == "temp_sensor_1"

    def test_sensors_get_by_name_not_found(self, sensors_collection):
        """Sensors should return None for non-existent sensor."""
        found = sensors_collection.getSensor("nonexistent")
        assert found is None

    def test_sensors_iteration(self, sensors_collection, mock_sensor_device_1, mock_sensor_device_2, mock_db_singleton):
        """Sensors should allow iteration over sensor list."""
        sensor1 = Sensor(mock_sensor_device_1)
        sensor2 = Sensor(mock_sensor_device_2)

        sensors_collection.addSensor(sensor1)
        sensors_collection.addSensor(sensor2)

        sensor_list = list(sensors_collection.sensors)
        assert len(sensor_list) == 2
        assert sensor1 in sensor_list
        assert sensor2 in sensor_list

    def test_sensors_collect_status(self, sensors_collection, mock_sensor_device_1, mock_sensor_device_2, mock_db_singleton):
        """Sensors should collect status from all sensors."""
        sensor1 = Sensor(mock_sensor_device_1)
        sensor2 = Sensor(mock_sensor_device_2)

        sensors_collection.addSensor(sensor1)
        sensors_collection.addSensor(sensor2)

        status = sensors_collection.collectSensorStatus()

        assert status["temp_sensor_1"] == 25.5
        assert status["temp_sensor_2"] == 30.0

    def test_sensors_mqtt_message(self, sensors_collection, mock_sensor_device_1, mock_sensor_device_2, mock_db_singleton):
        """Sensors should generate JSON MQTT message."""
        sensor1 = Sensor(mock_sensor_device_1)
        sensor2 = Sensor(mock_sensor_device_2)

        sensors_collection.addSensor(sensor1)
        sensors_collection.addSensor(sensor2)

        mqtt_message = sensors_collection.getMQTTMessage()

        # Should be valid JSON
        parsed = json.loads(mqtt_message)
        assert parsed["temp_sensor_1"] == 25.5
        assert parsed["temp_sensor_2"] == 30.0

    def test_sensors_log_to_db(self, sensors_collection, mock_sensor_device_1, mock_db_singleton):
        """Sensors should trigger logging on all sensors."""
        sensor1 = Sensor(mock_sensor_device_1)

        # Mock the logSensorToDb method
        sensor1.logSensorToDb = Mock()

        sensors_collection.addSensor(sensor1)
        sensors_collection.logSensorsToDb()

        # Should have called logSensorToDb on sensor
        sensor1.logSensorToDb.assert_called_once()

    def test_sensors_empty_collection_status(self):
        """Sensors should handle empty collection gracefully."""
        sensors = Sensors()

        status = sensors.collectSensorStatus()
        assert status == {}

    def test_sensors_empty_collection_mqtt(self):
        """Sensors should return empty JSON for empty collection."""
        sensors = Sensors()

        mqtt_message = sensors.getMQTTMessage()
        parsed = json.loads(mqtt_message)

        assert parsed == {}

    def test_sensors_multiple_sensors_same_name(self, sensors_collection, mock_db_singleton):
        """Sensors should handle multiple sensors (getSensor returns first match)."""
        # Create two devices with same name
        device1 = Mock()
        device1.getName.return_value = "duplicate"
        device1.getCurrentReading.return_value = 10.0
        device1.status.return_value = {"duplicate": 10.0}

        device2 = Mock()
        device2.getName.return_value = "duplicate"
        device2.getCurrentReading.return_value = 20.0
        device2.status.return_value = {"duplicate": 20.0}

        sensor1 = Sensor(device1)
        sensor2 = Sensor(device2)

        sensors_collection.addSensor(sensor1)
        sensors_collection.addSensor(sensor2)

        # getSensor returns first match
        found = sensors_collection.getSensor("duplicate")
        assert found == sensor1
