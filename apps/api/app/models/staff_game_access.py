from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class StaffGameAccess(Base):
    __tablename__ = "admin_user_game_access"
    __table_args__ = (
        UniqueConstraint(
            "admin_user_id",
            "game_id",
            name="uq_admin_user_game_access_admin_user_id_game_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(
        Integer,
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    admin_user = relationship("AdminUser", back_populates="game_access")
    game = relationship("Game")
