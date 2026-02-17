from __future__ import annotations

from dataclasses import dataclass

VAL_ROLE_OPTIONS = {"Duelist", "Initiator", "Controller", "Sentinel", "IGL", "Flex"}

# Order matters
_TIER_ORDER = [
    "Iron", "Bronze", "Silver", "Gold", "Platinum",
    "Diamond", "Ascendant", "Immortal", "Radiant"
]

def valorant_rank_to_numeric(rank_label: str) -> float:
    """
    Converts rank like 'Diamond 2' or 'Radiant' to 0-100 scale.
    Returns 0 if unknown.
    """
    if not rank_label:
        return 0.0

    s = rank_label.strip()
    parts = s.split()

    tier = parts[0].capitalize()
    if tier not in _TIER_ORDER:
        return 0.0

    if tier == "Radiant":
        return 100.0

    # Default division is 1 if missing
    div = 1
    if len(parts) >= 2:
        try:
            div = int(parts[1])
        except ValueError:
            div = 1
    div = max(1, min(3, div))

    tier_index = _TIER_ORDER.index(tier)  # 0..8
    # Radiant handled above, so max tier_index here is Immortal index 7
    # Each tier gets an interval, each division bumps within tier
    base = (tier_index / (len(_TIER_ORDER) - 1)) * 100.0  # includes Radiant tier, but ok
    bump = (div - 1) * 2.5  # small within-tier bump
    numeric = min(99.0, base + bump)  # Radiant is 100
    return round(numeric, 2)

@dataclass
class ValorantInputs:
    rank_numeric: float
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool
    team_experience: bool
    scrim_experience: bool
    tournament_experience: str  # none/local/regional/national
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

def score_valorant(inputs: ValorantInputs) -> tuple[float, dict]:
    """
    Returns (score_0_to_100, explanation_json)
    """
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
