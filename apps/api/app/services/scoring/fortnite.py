from dataclasses import dataclass
from typing import Any

from app.services.scoring.contracts import ScoringResult, make_component, make_explanation

FORTNITE_ROLE_OPTIONS = {"IGL", "Fragger", "Support", "Flex"}

def fortnite_rank_to_numeric(rank_label: str) -> float:
    if not rank_label:
        return 0.0

    rank_map = {
        "Bronze": 15.0,
        "Silver": 30.0,
        "Gold": 45.0,
        "Platinum": 60.0,
        "Diamond": 75.0,
        "Elite": 85.0,
        "Champion": 92.0,
        "Unreal": 100.0,
    }

    return rank_map.get(rank_label.strip().title(), 0.0)

@dataclass
class FortniteInputs:
    rank_numeric: float
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool
    team_experience: bool
    scrim_experience: bool
    tournament_experience: str
    tracker_url_present: bool
    ign_present: bool
    roles_present: bool
    peak_rank_present: bool

def _availability_score(hours_per_week: int, wn: bool, we: bool) -> float:
    h = max(0, min(20, hours_per_week))
    base = (min(h, 12) / 12) * 100.0
    if wn:
        base += 10
    if we:
        base += 5
    return float(max(0.0, min(100.0, base)))

def _tourney_score(level: str) -> float:
    m = {
        "none": 0.0,
        "local": 35.0,
        "regional": 70.0,
        "national": 90.0,
    }
    return m.get((level or "none").lower().strip(), 0.0)

def _experience_score(team: bool, scrim: bool, tourney: str) -> float:
    score = 0.0
    score += 25.0 if team else 0.0
    score += 25.0 if scrim else 0.0
    score += _tourney_score(tourney)
    return float(max(0.0, min(100.0, score)))

def _completeness_score(tracker: bool, ign: bool, roles: bool, peak: bool) -> float:
    score = 0.0
    score += 30.0 if ign else 0.0
    score += 30.0 if roles else 0.0
    score += 20.0 if tracker else 0.0
    score += 20.0 if peak else 0.0
    return float(max(0.0, min(100.0, score)))


def _build_inputs(payload: Any) -> tuple[FortniteInputs, float, float | None, dict[str, Any]]:
    current_rank_numeric = fortnite_rank_to_numeric(payload.profile.current_rank_label)
    peak_rank_numeric = (
        fortnite_rank_to_numeric(payload.profile.peak_rank_label)
        if payload.profile.peak_rank_label
        else None
    )

    return (
        FortniteInputs(
            rank_numeric=current_rank_numeric,
            hours_per_week=payload.availability.hours_per_week,
            weeknights_available=payload.availability.weeknights_available,
            weekends_available=payload.availability.weekends_available,
            team_experience=payload.profile.team_experience,
            scrim_experience=payload.profile.scrim_experience,
            tournament_experience=payload.profile.tournament_experience,
            tracker_url_present=bool(payload.profile.tracker_url),
            ign_present=bool(payload.profile.ign),
            roles_present=bool(payload.profile.primary_role),
            peak_rank_present=bool(payload.profile.peak_rank_label),
        ),
        current_rank_numeric,
        peak_rank_numeric,
        {
            "current_rank_label": payload.profile.current_rank_label,
            "peak_rank_label": payload.profile.peak_rank_label,
            "fortnite_mode": payload.profile.fortnite_mode,
            "hours_per_week": payload.availability.hours_per_week,
            "weeknights_available": payload.availability.weeknights_available,
            "weekends_available": payload.availability.weekends_available,
            "team_experience": payload.profile.team_experience,
            "scrim_experience": payload.profile.scrim_experience,
            "tournament_experience": payload.profile.tournament_experience,
            "tracker_url_present": bool(payload.profile.tracker_url),
            "ign_present": bool(payload.profile.ign),
            "roles_present": bool(payload.profile.primary_role),
            "peak_rank_present": bool(payload.profile.peak_rank_label),
        },
    )


def score_fortnite(payload: Any) -> ScoringResult:
    inputs, current_rank_numeric, peak_rank_numeric, raw_inputs = _build_inputs(payload)
    rank = float(max(0.0, min(100.0, inputs.rank_numeric)))
    availability = _availability_score(
        inputs.hours_per_week,
        inputs.weeknights_available,
        inputs.weekends_available,
    )
    experience = _experience_score(
        inputs.team_experience,
        inputs.scrim_experience,
        inputs.tournament_experience,
    )
    complete = _completeness_score(
        inputs.tracker_url_present,
        inputs.ign_present,
        inputs.roles_present,
        inputs.peak_rank_present,
    )

    total = (
        0.55 * rank +
        0.20 * availability +
        0.15 * experience +
        0.10 * complete
    )

    explanation = make_explanation(
        {
            "skill": make_component(rank, 0.55),
            "availability": make_component(availability, 0.20),
            "experience": make_component(experience, 0.15),
            "completeness": make_component(complete, 0.10),
        },
        total,
    )

    return ScoringResult(
        score=round(float(total), 2),
        explanation=explanation,
        model_version="v1_fortnite",
        scoring_method="rules",
        raw_inputs=raw_inputs,
        normalized_features={
            "rank_numeric": rank,
            "availability": availability,
            "experience": experience,
            "completeness": complete,
        },
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=peak_rank_numeric,
    )
