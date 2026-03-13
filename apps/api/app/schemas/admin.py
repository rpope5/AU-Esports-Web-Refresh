from pydantic import BaseModel
from typing import Optional

class RecruitStatusUpdate(BaseModel):
    status: str

class RecruitNotesUpdate(BaseModel):
    notes: Optional[str] = None