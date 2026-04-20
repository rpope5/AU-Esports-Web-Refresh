from pydantic import BaseModel
from pydantic import Field

class LoginRequest(BaseModel):
    username: str
    password: str


class PermissionPayload(BaseModel):
    can_view_recruits: bool
    can_manage_recruits: bool
    can_delete_recruits: bool
    can_view_roster: bool
    can_manage_roster: bool
    can_delete_roster: bool
    can_manage_announcements: bool
    can_delete_announcements: bool
    can_manage_schedule: bool
    can_delete_schedule: bool
    can_manage_users: bool


class AuthResponse(BaseModel):
    access_token: str
    role: str
    username: str
    must_change_password: bool = False
    allowed_game_slugs: list[str] = Field(default_factory=list)
    has_global_game_access: bool = False
    permissions: PermissionPayload
