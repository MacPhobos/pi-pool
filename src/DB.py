"""Database interface using SQLAlchemy ORM.

Maintains exact same public API as original psycopg2 implementation for compatibility.
"""

import logging
from datetime import datetime
from db.Engine import Engine
from db.models.DeviceRuntime import DeviceRuntime
from db.models.SensorReading import SensorReading
from db.models.Event import Event


class DB:
    """Database singleton wrapper for SQLAlchemy operations.

    Provides same interface as original psycopg2 implementation:
    - logDuration(topic, startTime, elapsedSeconds)
    - logSensor(sensorName, reading)
    - logStateChangeEvent(name, state_from, state_to)
    - logOpaqueEvent(name, opaque)
    """

    __instance = None

    @staticmethod
    def getInstance():
        """Static access method."""
        if DB.__instance is None:
            raise Exception("Instantiate first")
        return DB.__instance

    def __init__(self, config):
        """Initialize database engine from config object.

        Args:
            config: Config object with dbName, dbUser, dbPassword attributes
        """
        # Initialize SQLAlchemy engine singleton
        self.engine = Engine(
            dbName=config.dbName,
            dbUser=config.dbUser,
            dbPassword=config.dbPassword,
            dbHost=getattr(config, 'dbHost', 'localhost')
        )

        if DB.__instance is not None:
            raise Exception("Singleton already initialized")
        else:
            DB.__instance = self

    def logDuration(self, topic, startTime, elapsedSeconds):
        """Log device runtime duration.

        Args:
            topic: Device topic (e.g., 'pump', 'heater')
            startTime: Start timestamp (datetime object)
            elapsedSeconds: Duration in seconds
        """
        if elapsedSeconds == 0:
            return

        try:
            with self.engine.getSession() as session:
                record = DeviceRuntime(
                    topic=topic,
                    start_time=startTime,
                    elapsed_seconds=elapsedSeconds
                )
                session.add(record)
                session.commit()
        except Exception as e:
            logging.error(f"Failed to log duration for {topic}: {e}")

    def logSensor(self, sensorName, reading):
        """Log sensor reading.

        Args:
            sensorName: Sensor identifier (e.g., 'temp_sensor_in')
            reading: Sensor reading value (float)
        """
        try:
            with self.engine.getSession() as session:
                record = SensorReading(
                    sensor=sensorName,
                    reading=reading
                )
                session.add(record)
                session.commit()
        except Exception as e:
            logging.error(f"Failed to log sensor {sensorName}: {e}")

    def logStateChangeEvent(self, name, state_from, state_to):
        """Log state change event.

        Args:
            name: Event name (e.g., 'pump', 'heater')
            state_from: Previous state
            state_to: New state
        """
        try:
            with self.engine.getSession() as session:
                record = Event(
                    name=name,
                    state_from=state_from,
                    state_to=state_to,
                    opaque=None
                )
                session.add(record)
                session.commit()
        except Exception as e:
            logging.error(f"Failed to log state change event {name}: {e}")

    def logOpaqueEvent(self, name, opaque):
        """Log opaque event (non-state-change event).

        Args:
            name: Event name
            opaque: Opaque data string
        """
        try:
            with self.engine.getSession() as session:
                record = Event(
                    name=name,
                    state_from=None,
                    state_to=None,
                    opaque=opaque
                )
                session.add(record)
                session.commit()
        except Exception as e:
            logging.error(f"Failed to log opaque event {name}: {e}")
