from dataclasses import dataclass
import re
from typing import Any

from app.services.scoring.contracts import ScoringResult, make_component, make_explanation

CS2_ROLE_OPTIONS = {"Entry", "AWPer", "IGL", "Lurker", "Support", "Flex"}

def cs2_rank_to_numeric(rank_label: str) -> float:
    if not rank_label:
        return 0.0

    s = rank_label.strip()

    premier_match = re.match(r"(?i)premier\s+(\d+)", s)
    if premier_match:
        rating = int(premier_match.group(1))
        rating = max(0, min(30000, rating))
        return round((rating / 30000) * 100, 2)

    faceit_match = re.match(r"(?i)faceit\s+(\d+)", s)
    if faceit_match:
        level = int(faceit_match.group(1))
        level = max(1, min(10, level))
        return round((level / 10) * 100, 2)

    rank_map = {
        "Silver 1": 10,
        "Silver 2": 15,
        "Silver 3": 20,
        "Silver 4": 25,
        "Silver Elite": 30,
        "Silver Elite Master": 35,
        "Gold Nova 1": 40,
        "Gold Nova 2": 45,
        "Gold Nova 3": 50,
        "Gold Nova Master": 55,
        "Master Guardian 1": 60,
        "Master Guardian 2": 65,
        "MGE": 70,
        "DMG": 75,
        "LE": 80,
        "LEM": 85,
        "Supreme": 92,
        "Global Elite": 100,
    }

    return float(rank_map.get(s, 0.0))

@dataclass
class CS2Inputs:
    rank_numeric: float
    faceit_level: int | None
    faceit_elo: int | None
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
    prior_team_history_present: bool

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
        "national": 90.0
    }
    return m.get((level or "none").lower().strip(), 0.0)

def _experience_score(team: bool, scrim: bool, tourney: str) -> float:
    score = 0.0
    score += 25.0 if team else 0.0
    score += 25.0 if scrim else 0.0
    score += _tourney_score(tourney)
    return float(max(0.0, min(100.0, score)))

def _faceit_level_score(faceit_level: int | None) -> float:
    if faceit_level is None:
        return 0.0
    level = max(1, min(10, int(faceit_level)))
    return round((level / 10) * 100.0, 2)


def _faceit_elo_score(faceit_elo: int | None) -> float:
    if faceit_elo is None:
        return 0.0
    elo = max(600, min(3000, int(faceit_elo)))
    return round(((elo - 600) / (3000 - 600)) * 100.0, 2)


def _weighted_average(values: list[tuple[float, float]]) -> float:
    used = [(value, weight) for value, weight in values if weight > 0]
    if not used:
        return 0.0
    total_weight = sum(weight for _, weight in used)
    if total_weight <= 0:
        return 0.0
    return float(sum(value * weight for value, weight in used) / total_weight)


def _skill_score(rank_numeric: float, faceit_level: int | None, faceit_elo: int | None) -> tuple[float, float, float]:
    level_score = _faceit_level_score(faceit_level)
    elo_score = _faceit_elo_score(faceit_elo)

    rank_weight = 0.35 if rank_numeric > 0 else 0.0
    level_weight = 0.25 if faceit_level is not None else 0.0
    elo_weight = 0.40 if faceit_elo is not None else 0.0

    skill = _weighted_average(
        [
            (rank_numeric, rank_weight),
            (level_score, level_weight),
            (elo_score, elo_weight),
        ]
    )
    return float(max(0.0, min(100.0, skill))), level_score, elo_score


def _experience_score_with_history(team: bool, scrim: bool, tourney: str, prior_team_history_present: bool) -> float:
    score = _experience_score(team, scrim, tourney)
    if prior_team_history_present:
        score += 10.0
    return float(max(0.0, min(100.0, score)))


def _completeness_score(
    tracker: bool,
    ign: bool,
    roles: bool,
    peak: bool,
    faceit_level_present: bool,
    faceit_elo_present: bool,
    prior_team_history_present: bool,
) -> float:
    # Preserve legacy completeness behavior as baseline and add small CS2-specific bonuses.
    base = 0.0
    base += 30.0 if ign else 0.0
    base += 30.0 if roles else 0.0
    base += 20.0 if tracker else 0.0
    base += 20.0 if peak else 0.0

    bonus = 0.0
    bonus += 10.0 if faceit_level_present else 0.0
    bonus += 10.0 if faceit_elo_present else 0.0
    bonus += 5.0 if prior_team_history_present else 0.0
    return float(max(0.0, min(100.0, base + bonus)))


def _build_inputs(payload: Any) -> tuple[CS2Inputs, float, float | None, dict[str, Any]]:
    current_rank_numeric = cs2_rank_to_numeric(payload.profile.current_rank_label)
    peak_rank_numeric = (
        cs2_rank_to_numeric(payload.profile.peak_rank_label)
        if payload.profile.peak_rank_label
        else None
    )

    return (
        CS2Inputs(
            rank_numeric=current_rank_numeric,
            faceit_level=payload.profile.faceit_level,
            faceit_elo=payload.profile.faceit_elo,
            hours_per_week=payload.availability.hours_per_week,
            weeknights_available=payload.availability.weeknights_available,
            weekends_available=payload.availability.weekends_available,
            team_experience=payload.profile.team_experience,
            scrim_experience=payload.profile.scrim_experience,
            tournament_experience=payload.profile.tournament_experience,
            tracker_url_present=bool(payload.profile.tracker_url),
            ign_present=bool(payload.profile.ign),
            roles_present=bool(payload.profile.primary_role or payload.profile.secondary_role or payload.profile.cs2_roles),
            peak_rank_present=bool(payload.profile.peak_rank_label),
            prior_team_history_present=bool(payload.profile.prior_team_history),
        ),
        current_rank_numeric,
        peak_rank_numeric,
        {
            "current_rank_label": payload.profile.current_rank_label,
            "peak_rank_label": payload.profile.peak_rank_label,
            "faceit_level": payload.profile.faceit_level,
            "faceit_elo": payload.profile.faceit_elo,
            "cs2_roles": payload.profile.cs2_roles,
            "prior_team_history": payload.profile.prior_team_history,
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


def score_cs2(payload: Any) -> ScoringResult:
    inputs, current_rank_numeric, peak_rank_numeric, raw_inputs = _build_inputs(payload)
    rank, faceit_level_score, faceit_elo_score = _skill_score(
        float(max(0.0, min(100.0, inputs.rank_numeric))),
        inputs.faceit_level,
        inputs.faceit_elo,
    )
    availability = _availability_score(inputs.hours_per_week, inputs.weeknights_available, inputs.weekends_available)
    experience = _experience_score_with_history(
        inputs.team_experience,
        inputs.scrim_experience,
        inputs.tournament_experience,
        inputs.prior_team_history_present,
    )
    complete = _completeness_score(
        inputs.tracker_url_present,
        inputs.ign_present,
        inputs.roles_present,
        inputs.peak_rank_present,
        inputs.faceit_level is not None,
        inputs.faceit_elo is not None,
        inputs.prior_team_history_present,
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
        model_version="v2_cs2",
        scoring_method="rules",
        raw_inputs=raw_inputs,
        normalized_features={
            "rank_numeric": rank,
            "faceit_level_score": faceit_level_score,
            "faceit_elo_score": faceit_elo_score,
            "availability": availability,
            "experience": experience,
            "completeness": complete,
        },
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=peak_rank_numeric,
    )
