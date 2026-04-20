from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False, index=True)
    game = Column(String(100), nullable=True)
    game_id = Column(
        Integer,
        ForeignKey("games.id"),
        nullable=True,
        index=True,
    )
    status = Column(String(32), nullable=False, default="published", index=True)
    created_by_admin_id = Column(
        Integer,
        ForeignKey("admin_users.id"),
        nullable=True,
    )
    approved_by_admin_id = Column(
        Integer,
        ForeignKey("admin_users.id"),
        nullable=True,
    )
    rejected_by_admin_id = Column(
        Integer,
        ForeignKey("admin_users.id"),
        nullable=True,
    )
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
