from dataclasses import dataclass
from typing import Any

from app.services.scoring.contracts import ScoringResult, make_component, make_explanation

def mario_kart_rank_to_numeric(lounge_rating: int | None) -> float:
    if not lounge_rating:
        return 0.0

    rating = max(0, min(10000, lounge_rating))

    if rating >= 9000:
        return 100.0
    if rating >= 8000:
        return 92.0
    if rating >= 7000:
        return 84.0
    if rating >= 6000:
        return 75.0
    if rating >= 5000:
        return 65.0
    if rating >= 4000:
        return 55.0
    if rating >= 3000:
        return 45.0
    if rating >= 2000:
        return 35.0
    return 20.0


@dataclass
class MarioKartInputs:
    lounge_rating: int | None
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool
    team_experience: bool
    scrim_experience: bool
    tournament_experience: str
    tracker_url_present: bool
    ign_present: bool
    preferred_title_present: bool
    controller_present: bool
    playstyle_present: bool


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


def _completeness_score(
    tracker: bool,
    ign: bool,
    preferred_title: bool,
    controller: bool,
    playstyle: bool,
) -> float:
    score = 0.0
    score += 25.0 if ign else 0.0
    score += 20.0 if tracker else 0.0
    score += 20.0 if preferred_title else 0.0
    score += 20.0 if controller else 0.0
    score += 15.0 if playstyle else 0.0
    return float(max(0.0, min(100.0, score)))


def _build_inputs(payload: Any) -> tuple[MarioKartInputs, float, dict[str, Any]]:
    current_rank_numeric = float(payload.profile.lounge_rating or 0)
    return (
        MarioKartInputs(
            lounge_rating=payload.profile.lounge_rating,
            hours_per_week=payload.availability.hours_per_week,
            weeknights_available=payload.availability.weeknights_available,
            weekends_available=payload.availability.weekends_available,
            team_experience=payload.profile.team_experience,
            scrim_experience=payload.profile.scrim_experience,
            tournament_experience=payload.profile.tournament_experience,
            tracker_url_present=bool(payload.profile.tracker_url),
            ign_present=bool(payload.profile.ign),
            preferred_title_present=bool(payload.profile.preferred_title),
            controller_present=bool(payload.profile.controller_type),
            playstyle_present=bool(payload.profile.playstyle),
        ),
        current_rank_numeric,
        {
            "lounge_rating": payload.profile.lounge_rating,
            "hours_per_week": payload.availability.hours_per_week,
            "weeknights_available": payload.availability.weeknights_available,
            "weekends_available": payload.availability.weekends_available,
            "team_experience": payload.profile.team_experience,
            "scrim_experience": payload.profile.scrim_experience,
            "tournament_experience": payload.profile.tournament_experience,
            "tracker_url_present": bool(payload.profile.tracker_url),
            "ign_present": bool(payload.profile.ign),
            "preferred_title_present": bool(payload.profile.preferred_title),
            "controller_present": bool(payload.profile.controller_type),
            "playstyle_present": bool(payload.profile.playstyle),
        },
    )


def score_mario_kart(payload: Any) -> ScoringResult:
    inputs, current_rank_numeric, raw_inputs = _build_inputs(payload)
    rank = mario_kart_rank_to_numeric(inputs.lounge_rating)
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
        inputs.preferred_title_present,
        inputs.controller_present,
        inputs.playstyle_present,
    )

    total = (
        0.40 * rank +
        0.25 * experience +
        0.20 * availability +
        0.15 * complete
    )

    explanation = make_explanation(
        {
            "skill": make_component(rank, 0.40),
            "experience": make_component(experience, 0.25),
            "availability": make_component(availability, 0.20),
            "completeness": make_component(complete, 0.15),
        },
        total,
    )

    return ScoringResult(
        score=round(float(total), 2),
        explanation=explanation,
        model_version="v1_mario_kart",
        scoring_method="rules",
        raw_inputs=raw_inputs,
        normalized_features={
            "lounge_rating_score": rank,
            "experience": experience,
            "availability": availability,
            "completeness": complete,
        },
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=None,
    )
