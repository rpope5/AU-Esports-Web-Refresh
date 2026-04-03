from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from typing import Any

RecruitReviewStatus = Literal[
    "NEW",
    "REVIEWED",
    "CONTACTED",
    "TRYOUT",
    "WATCHLIST",
    "ACCEPTED",
    "REJECTED",
]

class RecruitStatusUpdate(BaseModel):
    status: RecruitReviewStatus
    label_reason: Optional[str] = None

class RecruitNotesUpdate(BaseModel):
    notes: Optional[str] = None


class RecruitScoreSummary(BaseModel):
    score: Optional[float] = None
    model_version: Optional[str] = None
    scoring_method: Optional[str] = None
    scored_at: Optional[datetime] = None
    is_current: Optional[bool] = None
    components: Optional[dict[str, Any]] = None


class RecruitScoreDetail(RecruitScoreSummary):
    explanation_json: Optional[dict[str, Any]] = None
    raw_inputs_json: Optional[dict[str, Any]] = None
    normalized_features_json: Optional[dict[str, Any]] = None
