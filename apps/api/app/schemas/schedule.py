from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ScheduleStatus = Literal["pending", "published", "rejected", "archived"]
ScheduleWorkflowAction = Literal[
    "submit_for_approval",
    "publish",
    "reject",
    "archive",
]


class CalendarEventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    time: datetime
    game_slug: str | None = Field(default=None, min_length=1, max_length=100)
    game: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("game_slug", "game", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class CalendarEventCreate(CalendarEventBase):
    workflow_action: ScheduleWorkflowAction | None = None


class CalendarEventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    time: datetime | None = None
    game_slug: str | None = Field(default=None, min_length=1, max_length=100)
    game: str | None = Field(default=None, max_length=100)
    workflow_action: ScheduleWorkflowAction | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("game_slug", "game", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None


class CalendarEventPublicOut(BaseModel):
    id: int
    name: str
    time: datetime
    game: str | None = None
    game_slug: str | None = None
    game_name: str | None = None
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalendarEventAdminOut(CalendarEventPublicOut):
    created_by_admin_id: int | None = None
    created_by_username: str | None = None
    approved_by_admin_id: int | None = None
    approved_by_username: str | None = None
    rejected_by_admin_id: int | None = None
    rejected_by_username: str | None = None
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    archived_at: datetime | None = None

