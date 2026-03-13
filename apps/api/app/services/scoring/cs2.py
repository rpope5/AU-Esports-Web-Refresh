from dataclasses import dataclass
import re

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
        "national": 90.0
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

def score_cs2(inputs: CS2Inputs) -> tuple[float, dict]:
    rank = float(max(0.0, min(100.0, inputs.rank_numeric)))
    availability = _availability_score(inputs.hours_per_week, inputs.weeknights_available, inputs.weekends_available)
    experience = _experience_score(inputs.team_experience, inputs.scrim_experience, inputs.tournament_experience)
    complete = _completeness_score(inputs.tracker_url_present, inputs.ign_present, inputs.roles_present, inputs.peak_rank_present)

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
            "completeness": complete
        }
    }

    return round(float(total), 2), explanation