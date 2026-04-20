from dataclasses import dataclass
from typing import Any

from app.services.scoring.contracts import ScoringResult, make_component, make_explanation

@dataclass
class SmashInputs:
    gsp: int
    regional_rank: str | None
    best_wins: str | None
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool
    tournament_experience: str
    tracker_url_present: bool
    characters_present: bool


def _gsp_score(gsp: int) -> float:
    if not gsp:
        return 0.0

    # rough scaling
    if gsp >= 14000000:
        return 100.0
    if gsp >= 13000000:
        return 90.0
    if gsp >= 12000000:
        return 80.0
    if gsp >= 11000000:
        return 65.0
    if gsp >= 10000000:
        return 50.0
    return 30.0


def _regional_score(regional_rank: str | None) -> float:
    if not regional_rank:
        return 0.0

    s = regional_rank.lower()

    if "top 10" in s:
        return 100.0
    if "top 25" in s:
        return 90.0
    if "top 50" in s:
        return 80.0
    if "top 100" in s:
        return 65.0

    return 40.0


def _wins_score(best_wins: str | None) -> float:
    if not best_wins:
        return 0.0

    # crude but effective: count number of names listed
    count = len([w for w in best_wins.split(",") if w.strip()])

    if count >= 5:
        return 100.0
    if count >= 3:
        return 85.0
    if count >= 1:
        return 65.0

        return 0.0


def _availability_score(hours, wn, we):
    base = min(100, (hours / 12) * 100)
    if wn:
        base += 10
    if we:
        base += 5
    return min(100, base)


def _tourney_score(level):
    return {
        "none": 0,
        "local": 40,
        "regional": 75,
        "national": 95,
    }.get(level, 0)


def _completeness(tracker, characters):
    score = 0
    if tracker:
        score += 50
    if characters:
        score += 50
    return score


def _build_inputs(payload: Any) -> tuple[SmashInputs, dict[str, Any]]:
    return (
        SmashInputs(
            gsp=payload.profile.gsp or 0,
            regional_rank=payload.profile.regional_rank,
            best_wins=payload.profile.best_wins,
            hours_per_week=payload.availability.hours_per_week,
            weeknights_available=payload.availability.weeknights_available,
            weekends_available=payload.availability.weekends_available,
            tournament_experience=payload.profile.tournament_experience,
            tracker_url_present=bool(payload.profile.tracker_url),
            characters_present=bool(payload.profile.characters),
        ),
        {
            "gsp": payload.profile.gsp or 0,
            "regional_rank": payload.profile.regional_rank,
            "best_wins": payload.profile.best_wins,
            "hours_per_week": payload.availability.hours_per_week,
            "weeknights_available": payload.availability.weeknights_available,
            "weekends_available": payload.availability.weekends_available,
            "tournament_experience": payload.profile.tournament_experience,
            "tracker_url_present": bool(payload.profile.tracker_url),
            "characters_present": bool(payload.profile.characters),
        },
    )


def score_smash(payload: Any) -> ScoringResult:
    inputs, raw_inputs = _build_inputs(payload)
    gsp = _gsp_score(inputs.gsp)
    regional = _regional_score(inputs.regional_rank)
    wins = _wins_score(inputs.best_wins)
    availability = _availability_score(
        inputs.hours_per_week,
        inputs.weeknights_available,
        inputs.weekends_available,
    )
    tourney = _tourney_score(inputs.tournament_experience)
    complete = _completeness(
        inputs.tracker_url_present,
        inputs.characters_present,
    )

    total = (
        0.25 * gsp +
        0.25 * regional +
        0.20 * wins +
        0.15 * tourney +
        0.10 * availability +
        0.05 * complete
    )

    explanation = make_explanation(
        {
            "skill_gsp": make_component(gsp, 0.25),
            "skill_regional": make_component(regional, 0.25),
            "skill_wins": make_component(wins, 0.20),
            "experience": make_component(tourney, 0.15),
            "availability": make_component(availability, 0.10),
            "completeness": make_component(complete, 0.05),
        },
        total,
    )

    return ScoringResult(
        score=round(total, 2),
        explanation=explanation,
        model_version="v1_smash",
        scoring_method="rules",
        raw_inputs=raw_inputs,
        normalized_features={
            "gsp_score": float(gsp),
            "regional_score": float(regional),
            "wins_score": float(wins),
            "experience": float(tourney),
            "availability": float(availability),
            "completeness": float(complete),
        },
        current_rank_numeric=None,
        peak_rank_numeric=None,
    )
