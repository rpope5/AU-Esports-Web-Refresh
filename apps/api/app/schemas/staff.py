from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


StaffCategory = Literal["coach", "captain", "faculty", "advisor", "staff", "other"]


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _normalize_string_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []

    source: list[str]
    if isinstance(value, str):
        source = [chunk.strip() for chunk in value.split(",")]
    else:
        source = value

    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in source:
        if not isinstance(raw, str):
            continue
        trimmed = raw.strip()
        if not trimmed:
            continue
        key = trimmed.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(trimmed)
    return cleaned


class StaffProfileBase(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    full_name: str = Field(min_length=1, max_length=160)
    preferred_name: str | None = Field(default=None, max_length=160)
    title: str = Field(min_length=1, max_length=160)
    category: StaffCategory = "other"
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    image_url: str | None = None
    game_scope: list[str] = Field(default_factory=list)
    year_label: str | None = Field(default=None, max_length=120)
    previous_college: str | None = Field(default=None, max_length=160)
    bio_at_ashland: list[str] = Field(default_factory=list)
    bio_before_ashland: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    sort_order: int = 0
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("slug is required")
        return normalized

    @field_validator("full_name", "title")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("preferred_name", "email", "phone", "image_url", "year_label", "previous_college")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: StaffCategory) -> StaffCategory:
        return value

    @field_validator("game_scope", "bio_at_ashland", "bio_before_ashland", "responsibilities", mode="before")
    @classmethod
    def validate_string_lists(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_string_list(value)


class StaffProfileCreate(StaffProfileBase):
    pass


class StaffProfileUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    preferred_name: str | None = Field(default=None, max_length=160)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    category: StaffCategory | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    image_url: str | None = None
    game_scope: list[str] | str | None = None
    year_label: str | None = Field(default=None, max_length=120)
    previous_college: str | None = Field(default=None, max_length=160)
    bio_at_ashland: list[str] | str | None = None
    bio_before_ashland: list[str] | str | None = None
    responsibilities: list[str] | str | None = None
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("slug is required")
        return normalized

    @field_validator("full_name", "title")
    @classmethod
    def validate_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("preferred_name", "email", "phone", "image_url", "year_label", "previous_college")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("game_scope", "bio_at_ashland", "bio_before_ashland", "responsibilities", mode="before")
    @classmethod
    def validate_string_lists(cls, value: list[str] | str | None) -> list[str] | None:
        if value is None:
            return None
        return _normalize_string_list(value)


class StaffProfileSummaryOut(BaseModel):
    id: int
    slug: str
    full_name: str
    preferred_name: str | None = None
    title: str
    category: StaffCategory
    email: str | None = None
    image_url: str | None = None
    game_scope: list[str] = Field(default_factory=list)
    year_label: str | None = None
    previous_college: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("game_scope", mode="before")
    @classmethod
    def normalize_game_scope(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_string_list(value)


class StaffProfileDetailOut(StaffProfileSummaryOut):
    phone: str | None = None
    bio_at_ashland: list[str] = Field(default_factory=list)
    bio_before_ashland: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("bio_at_ashland", "bio_before_ashland", "responsibilities", mode="before")
    @classmethod
    def normalize_detail_lists(cls, value: list[str] | str | None) -> list[str]:
        return _normalize_string_list(value)
