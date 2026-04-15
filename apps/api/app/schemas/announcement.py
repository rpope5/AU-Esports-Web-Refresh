from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

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
