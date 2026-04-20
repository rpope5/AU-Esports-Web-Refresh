from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

StaffAccountRole = Literal["admin", "head_coach", "coach", "captain"]


class UserScopeOut(BaseModel):
    game_id: int
    game_slug: str
    game_name: str


class ManagedUserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: StaffAccountRole
    is_active: bool
    must_change_password: bool
    has_global_game_access: bool
    scopes: list[UserScopeOut] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    manageable: bool = False


class ManagedUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(..., min_length=8, max_length=256)
    role: StaffAccountRole
    game_ids: list[int] = Field(default_factory=list)
    is_active: bool = True
    must_change_password: bool = True

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("username is required")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        return normalized or None


class ManagedUserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    role: StaffAccountRole | None = None
    game_ids: list[int] | None = None
    is_active: bool | None = None
    must_change_password: bool | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        return normalized or None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=256)
    must_change_password: bool = True


class UserManagementOptionsOut(BaseModel):
    viewer_role: StaffAccountRole
    assignable_roles: list[StaffAccountRole]
    scope_game_ids: list[int]
    scope_game_slugs: list[str]
    games: list[UserScopeOut]
