from pydantic import BaseModel
from typing import Optional, Literal


class AvailabilityInput(BaseModel):
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool


class RecruitProfileInput(BaseModel):
    ign: str
    current_rank_label: str
    peak_rank_label: Optional[str] = None
    primary_role: str
    secondary_role: Optional[str] = None
    tracker_url: Optional[str] = None
    team_experience: bool
    scrim_experience: bool
    tournament_experience: str
    fortnite_mode: str | None = None


class RecruitApplyInput(BaseModel):
    first_name: str
    last_name: str
    email: str
    discord: str
    current_school: Optional[str] = None
    graduation_year: Optional[int] = None
    preferred_contact: Optional[str] = None

    availability: AvailabilityInput
    game_slug: Literal["valorant", "cs2", "fortnite"]
    profile: RecruitProfileInput