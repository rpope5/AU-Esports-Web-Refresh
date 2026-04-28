from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, UniqueConstraint
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
    game_profiles = relationship(
        "PlayerGameProfile",
        back_populates="player",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PlayerGameProfile.id",
    )

    @property
    def primary_game_profile(self) -> "PlayerGameProfile | None":
        if self.game_profiles:
            for profile in self.game_profiles:
                if profile.is_primary and profile.game and profile.game.slug:
                    return profile
            for profile in self.game_profiles:
                if profile.game and profile.game.slug:
                    return profile
        return None

    @property
    def primary_game_slug(self) -> str | None:
        profile = self.primary_game_profile
        if profile and profile.game_slug:
            return profile.game_slug
        if self.primary_game and self.primary_game.slug:
            return self.primary_game.slug
        return None

    @property
    def primary_game_name(self) -> str | None:
        profile = self.primary_game_profile
        if profile and profile.game_name:
            return profile.game_name
        if self.primary_game and self.primary_game.name:
            return self.primary_game.name
        return self.game

    @property
    def secondary_game_slugs(self) -> list[str]:
        if self.game_profiles:
            primary_slug = self.primary_game_slug
            slugs: list[str] = []
            seen: set[str] = set()
            for profile in self.game_profiles:
                slug = profile.game_slug
                if not slug or slug == primary_slug or slug in seen:
                    continue
                seen.add(slug)
                slugs.append(slug)
            return slugs
        return [game.slug for game in self.secondary_games if game.slug]

    @property
    def secondary_game_names(self) -> list[str]:
        if self.game_profiles:
            primary_slug = self.primary_game_slug
            names: list[str] = []
            seen: set[str] = set()
            for profile in self.game_profiles:
                slug = profile.game_slug
                name = profile.game_name
                if not slug or not name or slug == primary_slug or slug in seen:
                    continue
                seen.add(slug)
                names.append(name)
            return names
        return [game.name for game in self.secondary_games if game.name]

    @property
    def primary_role(self) -> str | None:
        profile = self.primary_game_profile
        if profile:
            return profile.role
        return self.role

    @property
    def primary_rank(self) -> str | None:
        profile = self.primary_game_profile
        if profile:
            return profile.rank
        return self.rank


class PlayerGameProfile(Base):
    __tablename__ = "player_game_profiles"
    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_player_game_profiles_player_game"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    player = relationship("Player", back_populates="game_profiles")
    game = relationship("Game", lazy="joined")

    @property
    def game_slug(self) -> str | None:
        if self.game and self.game.slug:
            return self.game.slug
        return None

    @property
    def game_name(self) -> str | None:
        if self.game and self.game.name:
            return self.game.name
        return None
