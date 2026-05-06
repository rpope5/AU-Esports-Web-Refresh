from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.types import JSON

from app.db.base import Base


class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    full_name = Column(String(160), nullable=False)
    preferred_name = Column(String(160), nullable=True)
    title = Column(String(160), nullable=False)
    category = Column(String(32), nullable=False, default="other", index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    image_url = Column(String, nullable=True)
    game_scope = Column(JSON, nullable=True)
    year_label = Column(String(120), nullable=True)
    previous_college = Column(String(160), nullable=True)
    bio_at_ashland = Column(JSON, nullable=True)
    bio_before_ashland = Column(JSON, nullable=True)
    responsibilities = Column(JSON, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
