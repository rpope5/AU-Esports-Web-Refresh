from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class LegacyRoster(Base):
    __tablename__ = "legacy_rosters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by_admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)

    players = relationship(
        "LegacyRosterPlayer",
        back_populates="legacy_roster",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="LegacyRosterPlayer.sort_order, LegacyRosterPlayer.id",
    )

    @property
    def player_count(self) -> int:
        return len(self.players or [])


class LegacyRosterPlayer(Base):
    __tablename__ = "legacy_roster_players"

    id = Column(Integer, primary_key=True, index=True)
    legacy_roster_id = Column(
        Integer,
        ForeignKey("legacy_rosters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    gamertag = Column(String, nullable=False)
    game = Column(String, nullable=False)
    primary_game_slug = Column(String, nullable=True)
    primary_game_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    year = Column(String, nullable=True)
    major = Column(String, nullable=True)
    headshot = Column(String, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    legacy_roster = relationship("LegacyRoster", back_populates="players")
    game_profiles = relationship(
        "LegacyRosterPlayerGameProfile",
        back_populates="legacy_roster_player",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="LegacyRosterPlayerGameProfile.id",
    )

    @property
    def primary_game_profile(self) -> "LegacyRosterPlayerGameProfile | None":
        if self.game_profiles:
            for profile in self.game_profiles:
                if profile.is_primary and profile.game_slug:
                    return profile
            for profile in self.game_profiles:
                if profile.game_slug:
                    return profile
        return None

    @property
    def secondary_game_slugs(self) -> list[str]:
        if not self.game_profiles:
            return []
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

    @property
    def secondary_game_names(self) -> list[str]:
        if not self.game_profiles:
            return []
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


class LegacyRosterPlayerGameProfile(Base):
    __tablename__ = "legacy_roster_player_game_profiles"
    __table_args__ = (
        UniqueConstraint(
            "legacy_roster_player_id",
            "game_slug",
            name="uq_legacy_roster_player_game_profiles_player_slug",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    legacy_roster_player_id = Column(
        Integer,
        ForeignKey("legacy_roster_players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_game_id = Column(Integer, ForeignKey("games.id", ondelete="SET NULL"), nullable=True, index=True)
    game_slug = Column(String, nullable=False)
    game_name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    rank = Column(String, nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    legacy_roster_player = relationship("LegacyRosterPlayer", back_populates="game_profiles")
