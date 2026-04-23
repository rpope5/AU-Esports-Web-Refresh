from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

AnnouncementState = Literal["draft", "pending_approval", "published", "rejected"]
AnnouncementWorkflowAction = Literal[
    "save_draft",
    "submit_for_approval",
    "publish",
    "reject",
]


class AnnouncementPublicOut(BaseModel):
    id: int
    title: str
    body: str
    image_url: str | None = None
    state: AnnouncementState
    game_slug: str | None = None
    game_name: str | None = None
    game_slugs: list[str] = Field(default_factory=list)
    game_names: list[str] = Field(default_factory=list)
    is_general: bool = False
    created_at: datetime
    updated_at: datetime | None = None


class AnnouncementAdminOut(AnnouncementPublicOut):
    created_by_admin_id: int | None = None
    created_by_username: str | None = None
    approved_by_admin_id: int | None = None
    approved_by_username: str | None = None
    approved_at: datetime | None = None


class AnnouncementUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, min_length=1)
    workflow_action: AnnouncementWorkflowAction | None = None
    game_slugs: list[str] | None = None
    is_general: bool | None = None

    @field_validator("game_slugs")
    @classmethod
    def normalize_game_slugs(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None

        normalized: list[str] = []
        seen: set[str] = set()
        for raw_slug in value:
            slug = raw_slug.strip().lower()
            if not slug:
                continue
            if slug in seen:
                continue
            seen.add(slug)
            normalized.append(slug)
        return normalized
