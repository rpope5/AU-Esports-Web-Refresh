from dataclasses import dataclass
from typing import Any


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


def make_component(raw_value: float, weight: float) -> dict[str, float]:
    raw = float(raw_value)
    return {
        "raw": round(raw, 2),
        "weight": float(weight),
        "contribution": round(raw * float(weight), 2),
    }


def make_explanation(components: dict[str, dict[str, float]], total: float) -> dict[str, Any]:
    return {
        "type": "rules_breakdown",
        "components": components,
        "total": round(float(total), 2),
    }
