from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False, index=True)
    game = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
