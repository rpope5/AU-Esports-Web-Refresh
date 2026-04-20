from typing import Any

from app.services.scoring.contracts import ScoringResult
from app.services.scoring.registry import SCORERS

def score_application(game_slug: str, payload: Any) -> ScoringResult:
    scorer = SCORERS.get(game_slug)
    if not scorer:
        raise ValueError("No scorer found for game")
    return scorer(payload)
