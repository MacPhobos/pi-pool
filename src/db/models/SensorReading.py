"""Sensor reading model."""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from ..Base import Base


class SensorReading(Base):
    """Model for sensor table.

    Stores temperature and other sensor readings with timestamps.
    """

    __tablename__ = 'sensor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor = Column(String)
    reading = Column(Float)
    time = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<SensorReading(id={self.id}, sensor='{self.sensor}', reading={self.reading})>"
