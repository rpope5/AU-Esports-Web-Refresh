from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class EsportsAnnouncement(Base):
    __tablename__ = "esports_announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    image_path = Column(String, nullable=True)
    state = Column(String(32), nullable=False, default="published")
    game_id = Column(
        Integer,
        ForeignKey("games.id"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    approved_by_admin_id = Column(
        Integer,
        ForeignKey("admin_users.id"),
        nullable=True,
    )
    approved_at = Column(DateTime, nullable=True)
    created_by_admin_id = Column(
        Integer,
        ForeignKey("admin_users.id"),
        nullable=True,
    )
