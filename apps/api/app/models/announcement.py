from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from app.db.base import Base

announcement_games = Table(
    "announcement_games",
    Base.metadata,
    Column(
        "announcement_id",
        Integer,
        ForeignKey("esports_announcements.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "game_id",
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


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
    is_general = Column(Boolean, nullable=False, default=False)
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

    primary_game = relationship("Game", foreign_keys=[game_id], lazy="joined")
    games = relationship("Game", secondary=announcement_games, lazy="selectin", order_by="Game.name")
