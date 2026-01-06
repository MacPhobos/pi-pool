"""Event logging model."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from ..Base import Base


class Event(Base):
    """Model for event table.

    Logs state changes and opaque events for devices and system operations.
    The opaque field accepts dict, str, or None and is stored as JSON.
    """

    __tablename__ = 'event'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    state_from = Column(String)
    state_to = Column(String)
    opaque = Column(JSON)
    time = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', state_from='{self.state_from}', state_to='{self.state_to}')>"
