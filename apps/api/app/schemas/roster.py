from pydantic import BaseModel, ConfigDict

class PlayerBase(BaseModel):
    name: str
    gamertag: str
    role: str | None = None
    rank: str | None = None
    game: str
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
    game: str | None = None
    year: str | None = None
    major: str | None = None
    headshot: str | None = None

class PlayerOut(PlayerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
