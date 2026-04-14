from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CalendarEventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    time: datetime
    game: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("game", mode="before")
    @classmethod
    def normalize_game(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class CalendarEventCreate(CalendarEventBase):
    pass


class CalendarEventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    time: datetime | None = None
    game: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("game", mode="before")
    @classmethod
    def normalize_game(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class CalendarEventOut(CalendarEventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
