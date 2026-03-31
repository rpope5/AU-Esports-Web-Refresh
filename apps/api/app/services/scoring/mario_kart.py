from dataclasses import dataclass

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


def score_mario_kart(inputs: MarioKartInputs) -> tuple[float, dict]:
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

    explanation = {
        "lounge_rating": round(0.40 * rank, 2),
        "experience": round(0.25 * experience, 2),
        "availability": round(0.20 * availability, 2),
        "completeness": round(0.15 * complete, 2),
        "raw": {
            "lounge_rating_score": rank,
            "experience": experience,
            "availability": availability,
            "completeness": complete,
        },
    }

    return round(float(total), 2), explanation