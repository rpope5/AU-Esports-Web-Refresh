from datetime import datetime

from pydantic import BaseModel


class AnnouncementPublicOut(BaseModel):
    id: int
    title: str
    body: str
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AnnouncementAdminOut(AnnouncementPublicOut):
    created_by_admin_id: int | None = None
    created_by_username: str | None = None
