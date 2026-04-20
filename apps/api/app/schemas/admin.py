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


class RecruitScoreComponentSummary(BaseModel):
    component: str
    raw: Optional[float] = None
    weight: Optional[float] = None
    contribution: Optional[float] = None


class RecruitTrainingExportRow(BaseModel):
    application_id: int
    game_id: int
    game_slug: str
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    scoring_method: Optional[str] = None
    model_version: Optional[str] = None
    scored_at: Optional[datetime] = None
    raw_inputs_json: Optional[dict[str, Any]] = None
    normalized_features_json: Optional[dict[str, Any]] = None
    explanation_json: Optional[dict[str, Any]] = None
    score_components_summary: Optional[list[RecruitScoreComponentSummary]] = None
    review_status: RecruitReviewStatus = "NEW"
    label_reason: Optional[str] = None
    labeled_at: Optional[datetime] = None
    reviewer_user_id: Optional[int] = None
    reviewer_username: Optional[str] = None


class RecruitTrainingExportResponse(BaseModel):
    count: int
    rows: list[RecruitTrainingExportRow]
