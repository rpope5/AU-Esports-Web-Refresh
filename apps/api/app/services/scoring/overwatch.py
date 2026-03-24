from dataclasses import dataclass

OVERWATCH_ROLE_OPTIONS = {"Tank", "DPS", "Support", "Flex"}

def overwatch_rank_to_numeric(rank_label: str) -> float:
    if not rank_label:
        return 0.0

    rank_map = {
        "Bronze": 12.0,
        "Silver": 24.0,
        "Gold": 38.0,
        "Platinum": 52.0,
        "Diamond": 68.0,
        "Master": 82.0,
        "Grandmaster": 94.0,
        "Top 500": 100.0,
    }

    return rank_map.get(rank_label.strip().title(), 0.0)

@dataclass
class OverwatchInputs:
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

def score_overwatch(inputs: OverwatchInputs) -> tuple[float, dict]:
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

    explanation = {
        "rank": round(0.55 * rank, 2),
        "availability": round(0.20 * availability, 2),
        "experience": round(0.15 * experience, 2),
        "completeness": round(0.10 * complete, 2),
        "raw": {
            "rank_numeric": rank,
            "availability": availability,
            "experience": experience,
            "completeness": complete,
        },
    }

    return round(float(total), 2), explanation