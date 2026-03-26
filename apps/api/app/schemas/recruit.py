from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Literal
from datetime import datetime


CURRENT_YEAR = datetime.now().year


class AvailabilityInput(BaseModel):
    hours_per_week: int = Field(..., ge=1, le=40)
    weeknights_available: bool
    weekends_available: bool


class RecruitProfileInput(BaseModel):
    ign: str = Field(..., min_length=1, max_length=50)
    current_rank_label: str = Field(..., min_length=1, max_length=50)
    peak_rank_label: Optional[str] = Field(default=None, max_length=50)
    primary_role: str = Field(..., min_length=1, max_length=50)
    secondary_role: Optional[str] = Field(default=None, max_length=100)
    tracker_url: Optional[str] = Field(default=None, max_length=255)
    team_experience: bool
    scrim_experience: bool
    tournament_experience: Literal["none", "local", "regional", "national"]
    fortnite_mode: str | None = None

    ranked_wins: Optional[int] = Field(default=None, ge=0, le=50000)
    years_played: Optional[int] = Field(default=None, ge=0, le=30)
    legend_peak_rank: Optional[int] = Field(default=None, ge=1, le=50000)
    preferred_format: Optional[str] = Field(default=None, max_length=50)
    other_card_games: Optional[str] = Field(default=None, max_length=255)
    


class RecruitApplyInput(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    discord: str = Field(..., min_length=2, max_length=50)
    current_school: Optional[str] = Field(default=None, max_length=100)
    graduation_year: Optional[int] = None
    preferred_contact: Optional[Literal["discord", "email"]] = None

    availability: AvailabilityInput
    game_slug: Literal[
        "valorant",
        "cs2",
        "fortnite",
        "r6",
        "rocket-league",
        "overwatch",
        "cod",
        "hearthstone",
    ]
    profile: RecruitProfileInput

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, v):
        if v is None:
            return v
        if v < CURRENT_YEAR or v > CURRENT_YEAR + 6:
            raise ValueError(f"graduation_year must be between {CURRENT_YEAR} and {CURRENT_YEAR + 6}")
        return v