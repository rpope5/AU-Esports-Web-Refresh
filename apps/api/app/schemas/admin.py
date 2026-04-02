from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Any

class RecruitStatusUpdate(BaseModel):
    status: str

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
