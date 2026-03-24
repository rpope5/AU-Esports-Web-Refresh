from pydantic import BaseModel

class PlayerBase(BaseModel):
    name: str
    gamertag: str
    role: str | None = None
    game: str
    year: str | None = None
    major: str | None = None
    headshot: str | None = None

class PlayerCreate(PlayerBase):
    pass

class PlayerOut(PlayerBase):
    id: int

    class Config:
        orm_mode = True