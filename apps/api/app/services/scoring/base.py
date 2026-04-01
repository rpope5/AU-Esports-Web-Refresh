from dataclasses import dataclass
from typing import Any

from app.services.scoring.registry import SCORERS


@dataclass
class ScoringResult:
    score: float
    explanation: dict[str, Any]
    model_version: str
    scoring_method: str
    raw_inputs: dict[str, Any]
    normalized_features: dict[str, Any]
    current_rank_numeric: float | None
    peak_rank_numeric: float | None


def score_application(game_slug: str, payload: Any) -> ScoringResult:
    config = SCORERS.get(game_slug)
    if not config:
        raise ValueError("No scorer found for game")

    prepared = config.prepare(payload)
    score, explanation = config.scorer(prepared.scorer_inputs)

    explanation_dict = explanation if isinstance(explanation, dict) else {}
    explanation_raw = explanation_dict.get("raw", {}) if isinstance(explanation_dict.get("raw", {}), dict) else {}

    normalized_features = prepared.normalized_features or explanation_raw

    return ScoringResult(
        score=float(score),
        explanation=explanation_dict,
        model_version=config.model_version,
        scoring_method="rules",
        raw_inputs=prepared.raw_inputs,
        normalized_features=normalized_features,
        current_rank_numeric=prepared.current_rank_numeric,
        peak_rank_numeric=prepared.peak_rank_numeric,
    )
