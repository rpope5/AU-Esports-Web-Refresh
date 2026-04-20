from pydantic import BaseModel, ConfigDict, Field


class GameOptionOut(BaseModel):
    id: int
    slug: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class PlayerBase(BaseModel):
    name: str
    gamertag: str
    role: str | None = None
    rank: str | None = None
    primary_game_slug: str
    secondary_game_slugs: list[str] = Field(default_factory=list)
    year: str | None = None
    major: str | None = None
    headshot: str | None = None

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: str | None = None
    gamertag: str | None = None
    role: str | None = None
    rank: str | None = None
    primary_game_slug: str | None = None
    secondary_game_slugs: list[str] | None = None
    year: str | None = None
    major: str | None = None
    headshot: str | None = None

class PlayerOut(PlayerBase):
    id: int
    game: str
    primary_game_slug: str | None = None
    primary_game_name: str | None = None
    secondary_game_names: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
