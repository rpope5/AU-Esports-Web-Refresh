from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from app.db.base import Base


player_secondary_games = Table(
    "player_secondary_games",
    Base.metadata,
    Column("player_id", Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gamertag = Column(String, nullable=False)
    role = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    game = Column(String, nullable=False)
    primary_game_id = Column(Integer, ForeignKey("games.id"), nullable=True, index=True)
    year = Column(String, nullable=True)
    major = Column(String, nullable=True)
    headshot = Column(String, nullable=True)  # URL or filename

    primary_game = relationship("Game", foreign_keys=[primary_game_id], lazy="joined")
    secondary_games = relationship(
        "Game",
        secondary=player_secondary_games,
        lazy="selectin",
        order_by="Game.name",
    )

    @property
    def primary_game_slug(self) -> str | None:
        if self.primary_game and self.primary_game.slug:
            return self.primary_game.slug
        return None

    @property
    def primary_game_name(self) -> str | None:
        if self.primary_game and self.primary_game.name:
            return self.primary_game.name
        return self.game

    @property
    def secondary_game_slugs(self) -> list[str]:
        return [game.slug for game in self.secondary_games if game.slug]

    @property
    def secondary_game_names(self) -> list[str]:
        return [game.name for game in self.secondary_games if game.name]
