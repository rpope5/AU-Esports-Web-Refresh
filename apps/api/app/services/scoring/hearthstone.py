from dataclasses import dataclass
import re

HEARTHSTONE_CLASS_OPTIONS = {
    "Death Knight",
    "Demon Hunter",
    "Druid",
    "Hunter",
    "Mage",
    "Paladin",
    "Priest",
    "Rogue",
    "Shaman",
    "Warlock",
    "Warrior",
}

def hearthstone_rank_to_numeric(rank_label: str) -> float:
    if not rank_label:
        return 0.0

    s = rank_label.strip()

    if s.lower() == "legend":
        return 100.0

    match = re.match(r"^(Bronze|Silver|Gold|Platinum|Diamond)\s+(\d+)$", s, re.IGNORECASE)
    if not match:
        return 0.0

    tier = match.group(1).title()
    division = int(match.group(2))

    tier_bases = {
        "Bronze": 10.0,
        "Silver": 25.0,
        "Gold": 45.0,
        "Platinum": 65.0,
        "Diamond": 82.0,
    }

    base = tier_bases[tier]
    # Lower division number is better, so 1 > 10
    progress = (10 - max(1, min(10, division))) / 9
    return round(base + progress * 12, 2)

@dataclass
class HearthstoneInputs:
    rank_numeric: float
    ranked_wins: int
    years_played: int
    legend_peak_rank: int | None
    hours_per_week: int
    weeknights_available: bool
    weekends_available: bool
    tournament_experience: str
    tracker_url_present: bool
    ign_present: bool
    deck_info_present: bool

def _availability_score(hours_per_week: int, wn: bool, we: bool) -> float:
    h = max(0, min(20, hours_per_week))
    base = (min(h, 12) / 12) * 100.0
    if wn:
        base += 10
    if we:
        base += 5
    return float(max(0.0, min(100.0, base)))

def _wins_score(ranked_wins: int) -> float:
    w = max(0, min(5000, ranked_wins))
    return round((w / 5000) * 100, 2)

def _years_score(years_played: int) -> float:
    y = max(0, min(10, years_played))
    return round((y / 10) * 100, 2)

def _legend_bonus(legend_peak_rank: int | None) -> float:
    if not legend_peak_rank:
        return 0.0
    rank = max(1, min(50000, legend_peak_rank))
    if rank <= 100:
        return 100.0
    if rank <= 500:
        return 90.0
    if rank <= 1000:
        return 80.0
    if rank <= 5000:
        return 60.0
    return 40.0

def _tourney_score(level: str) -> float:
    m = {
        "none": 0.0,
        "local": 35.0,
        "regional": 70.0,
        "national": 90.0,
    }
    return m.get((level or "none").lower().strip(), 0.0)

def _completeness_score(tracker: bool, ign: bool, deck_info: bool) -> float:
    score = 0.0
    score += 40.0 if ign else 0.0
    score += 30.0 if tracker else 0.0
    score += 30.0 if deck_info else 0.0
    return float(max(0.0, min(100.0, score)))

def score_hearthstone(inputs: HearthstoneInputs) -> tuple[float, dict]:
    rank = float(max(0.0, min(100.0, inputs.rank_numeric)))
    wins = _wins_score(inputs.ranked_wins)
    years = _years_score(inputs.years_played)
    legend = _legend_bonus(inputs.legend_peak_rank)
    availability = _availability_score(
        inputs.hours_per_week,
        inputs.weeknights_available,
        inputs.weekends_available,
    )
    experience = max(_tourney_score(inputs.tournament_experience), (wins * 0.6 + years * 0.4))
    complete = _completeness_score(
        inputs.tracker_url_present,
        inputs.ign_present,
        inputs.deck_info_present,
    )

    total = (
        0.40 * rank +
        0.20 * experience +
        0.15 * availability +
        0.15 * complete +
        0.10 * legend
    )

    explanation = {
        "rank": round(0.40 * rank, 2),
        "experience": round(0.20 * experience, 2),
        "availability": round(0.15 * availability, 2),
        "completeness": round(0.15 * complete, 2),
        "legend_bonus": round(0.10 * legend, 2),
        "raw": {
            "rank_numeric": rank,
            "ranked_wins": wins,
            "years_played": years,
            "legend_bonus": legend,
            "availability": availability,
            "experience": experience,
            "completeness": complete,
        },
    }

    return round(float(total), 2), explanation