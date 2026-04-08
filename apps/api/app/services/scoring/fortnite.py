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
    epic_games_name_present: bool
    fortnite_pr: int | None
    fortnite_kd: float | None
    fortnite_total_kills: int | None
    fortnite_playtime_hours: float | None
    fortnite_wins: int | None
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

def _pr_score(pr: int | None) -> float:
    if pr is None:
        return 0.0
    p = max(0, int(pr))
    if p >= 10000:
        return 100.0
    if p >= 5000:
        return 85.0
    if p >= 2500:
        return 70.0
    if p >= 1000:
        return 55.0
    if p >= 500:
        return 40.0
    return 25.0 if p > 0 else 0.0


def _kd_score(kd: float | None) -> float:
    if kd is None:
        return 0.0
    value = max(0.0, min(8.0, float(kd)))
    return round((value / 8.0) * 100.0, 2)


def _wins_score(wins: int | None) -> float:
    if wins is None:
        return 0.0
    value = max(0, min(500, int(wins)))
    return round((value / 500) * 100.0, 2)


def _kills_score(kills: int | None) -> float:
    if kills is None:
        return 0.0
    value = max(0, min(20000, int(kills)))
    return round((value / 20000) * 100.0, 2)


def _playtime_score(playtime_hours: float | None) -> float:
    if playtime_hours is None:
        return 0.0
    value = max(0.0, min(2000.0, float(playtime_hours)))
    return round((value / 2000.0) * 100.0, 2)


def _weighted_average(values: list[tuple[float, float]]) -> float:
    used = [(value, weight) for value, weight in values if weight > 0]
    if not used:
        return 0.0
    total_weight = sum(weight for _, weight in used)
    if total_weight <= 0:
        return 0.0
    return float(sum(value * weight for value, weight in used) / total_weight)


def _skill_score(rank_numeric: float, pr: int | None, kd: float | None, wins: int | None) -> tuple[float, float, float, float]:
    pr_score = _pr_score(pr)
    kd_score = _kd_score(kd)
    wins_score = _wins_score(wins)
    skill = _weighted_average(
        [
            (rank_numeric, 0.35 if rank_numeric > 0 else 0.0),
            (pr_score, 0.35 if pr is not None else 0.0),
            (kd_score, 0.20 if kd is not None else 0.0),
            (wins_score, 0.10 if wins is not None else 0.0),
        ]
    )
    return float(max(0.0, min(100.0, skill))), pr_score, kd_score, wins_score


def _experience_score_with_tracker(team: bool, scrim: bool, tourney: str, total_kills: int | None, playtime_hours: float | None) -> tuple[float, float, float]:
    team_exp = _experience_score(team, scrim, tourney)
    kills_score = _kills_score(total_kills)
    playtime_score = _playtime_score(playtime_hours)
    combined = _weighted_average(
        [
            (team_exp, 0.50),
            (playtime_score, 0.30 if playtime_hours is not None else 0.0),
            (kills_score, 0.20 if total_kills is not None else 0.0),
        ]
    )
    return float(max(0.0, min(100.0, combined))), kills_score, playtime_score


def _completeness_score(
    tracker: bool,
    ign: bool,
    roles: bool,
    peak: bool,
    epic_name: bool,
    pr_present: bool,
    kd_present: bool,
    kills_present: bool,
    playtime_present: bool,
    wins_present: bool,
) -> float:
    # Preserve legacy completeness behavior as baseline and add tracker-data coverage bonus.
    base = 0.0
    base += 25.0 if ign else 0.0
    base += 20.0 if roles else 0.0
    base += 20.0 if tracker else 0.0
    base += 20.0 if peak else 0.0

    bonus = 0.0
    bonus += 8.0 if epic_name else 0.0
    bonus += 4.0 if pr_present else 0.0
    bonus += 4.0 if kd_present else 0.0
    bonus += 4.0 if kills_present else 0.0
    bonus += 4.0 if playtime_present else 0.0
    bonus += 4.0 if wins_present else 0.0
    return float(max(0.0, min(100.0, base + bonus)))


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
            epic_games_name_present=bool(payload.profile.epic_games_name),
            fortnite_pr=payload.profile.fortnite_pr,
            fortnite_kd=payload.profile.fortnite_kd,
            fortnite_total_kills=payload.profile.fortnite_total_kills,
            fortnite_playtime_hours=payload.profile.fortnite_playtime_hours,
            fortnite_wins=payload.profile.fortnite_wins,
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
            "epic_games_name": payload.profile.epic_games_name,
            "fortnite_pr": payload.profile.fortnite_pr,
            "fortnite_kd": payload.profile.fortnite_kd,
            "fortnite_total_kills": payload.profile.fortnite_total_kills,
            "fortnite_playtime_hours": payload.profile.fortnite_playtime_hours,
            "fortnite_wins": payload.profile.fortnite_wins,
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
    rank, pr_score, kd_score, wins_score = _skill_score(
        float(max(0.0, min(100.0, inputs.rank_numeric))),
        inputs.fortnite_pr,
        inputs.fortnite_kd,
        inputs.fortnite_wins,
    )
    availability = _availability_score(
        inputs.hours_per_week,
        inputs.weeknights_available,
        inputs.weekends_available,
    )
    experience, kills_score, playtime_score = _experience_score_with_tracker(
        inputs.team_experience,
        inputs.scrim_experience,
        inputs.tournament_experience,
        inputs.fortnite_total_kills,
        inputs.fortnite_playtime_hours,
    )
    complete = _completeness_score(
        inputs.tracker_url_present,
        inputs.ign_present,
        inputs.roles_present,
        inputs.peak_rank_present,
        inputs.epic_games_name_present,
        inputs.fortnite_pr is not None,
        inputs.fortnite_kd is not None,
        inputs.fortnite_total_kills is not None,
        inputs.fortnite_playtime_hours is not None,
        inputs.fortnite_wins is not None,
    )
    
    mode_bonus = 0.0

    preferred_mode = "builds"  # or pull this from config/db later

    player_mode = (raw_inputs.get("fortnite_mode") or "").lower()

    if preferred_mode in player_mode:
        mode_bonus = 8.0  # 5–10 range is good

    total = (
        0.45 * rank +
        0.10 * availability +
        0.40 * experience +
        0.05 * complete
    )
    total = min(100.0, total + mode_bonus)

    explanation = make_explanation(
        {
            "skill": make_component(rank, 0.45),
            "availability": make_component(availability, 0.10),
            "experience": make_component(experience, 0.40),
            "completeness": make_component(complete, 0.05),
        },
        total,
    )

    return ScoringResult(
        score=round(float(total), 2),
        explanation=explanation,
        model_version="v2_fortnite",
        scoring_method="rules",
        raw_inputs=raw_inputs,
        normalized_features={
            "rank_numeric": rank,
            "pr_score": pr_score,
            "kd_score": kd_score,
            "wins_score": wins_score,
            "kills_score": kills_score,
            "playtime_score": playtime_score,
            "availability": availability,
            "experience": experience,
            "completeness": complete,
        },
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=peak_rank_numeric,
    )
