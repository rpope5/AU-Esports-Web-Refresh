from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime


CURRENT_YEAR = datetime.now().year


class AvailabilityInput(BaseModel):
    hours_per_week: int = Field(..., ge=1, le=40)
    weeknights_available: bool
    weekends_available: bool


class RecruitProfileInput(BaseModel):
    ign: Optional[str] = Field(default=None, min_length=1, max_length=50)
    current_rank_label:Optional[str] = Field(default=None, min_length=1, max_length=50)
    peak_rank_label: Optional[str] = Field(default=None, max_length=50)
    primary_role: Optional[str] = Field(default=None, min_length=1, max_length=50)
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
    
    gsp: Optional[int] = Field(default=None, ge=0, le=16000000)
    regional_rank: Optional[str] = Field(default=None, max_length=100)
    best_wins: Optional[str] = Field(default=None, max_length=500)
    characters: Optional[str] = Field(default=None, max_length=500)
    
    lounge_rating: Optional[int] = Field(default=None, ge=0, le=10000)
    preferred_title: Optional[str] = Field(default=None, max_length=50)
    controller_type: Optional[str] = Field(default=None, max_length=50)
    playstyle: Optional[str] = Field(default=None, max_length=50)
    preferred_tracks: Optional[str] = Field(default=None, max_length=255)
    


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
        "smash",
        "mario-kart"
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
    
    @model_validator(mode="after")
    def validate_profile_by_game(self):
        if self.game_slug != "smash":
            if not self.profile.ign:
                raise ValueError("ign is required for this game")
            if not self.profile.current_rank_label:
                raise ValueError("current_rank_label is required for this game")
            if not self.profile.primary_role:
                raise ValueError("primary_role is required for this game")

        return self