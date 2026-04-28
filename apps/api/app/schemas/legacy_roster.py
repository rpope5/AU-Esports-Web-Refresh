from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LegacyRosterCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name is required")
        if len(normalized) > 120:
            raise ValueError("name must be 120 characters or fewer")
        return normalized


class LegacyRosterGameProfileOut(BaseModel):
    game_slug: str
    game_name: str
    role: str | None = None
    rank: str | None = None
    is_primary: bool = False

    model_config = ConfigDict(from_attributes=True)


class LegacyRosterPlayerOut(BaseModel):
    id: int
    original_player_id: int | None = None
    name: str
    gamertag: str
    game: str
    primary_game_slug: str | None = None
    primary_game_name: str | None = None
    secondary_game_slugs: list[str] = Field(default_factory=list)
    secondary_game_names: list[str] = Field(default_factory=list)
    role: str | None = None
    rank: str | None = None
    game_profiles: list[LegacyRosterGameProfileOut] = Field(default_factory=list)
    year: str | None = None
    major: str | None = None
    headshot: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LegacyRosterListItemOut(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime
    player_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class LegacyRosterDetailOut(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime
    players: list[LegacyRosterPlayerOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
