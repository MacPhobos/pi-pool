"""Device runtime logging model."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..Base import Base


class DeviceRuntime(Base):
    """Model for device_runtime table.

    Tracks runtime duration for pool devices (pump, heater, lights).
    """

    __tablename__ = 'device_runtime'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String)
    start_time = Column(DateTime, server_default=func.now())
    elapsed_seconds = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<DeviceRuntime(id={self.id}, topic='{self.topic}', elapsed_seconds={self.elapsed_seconds})>"
