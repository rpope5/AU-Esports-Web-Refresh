from __future__ import annotations

import argparse
import random
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.recruit import (
    RECRUIT_REVIEW_STATUSES,
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
    RecruitReview,
)
from app.schemas.recruit import RecruitApplyInput
from app.services.scoring.base import score_application
from app.services.scoring.cod import COD_ROLE_OPTIONS
from app.services.scoring.cs2 import CS2_ROLE_OPTIONS
from app.services.scoring.fortnite import FORTNITE_ROLE_OPTIONS
from app.services.scoring.hearthstone import HEARTHSTONE_CLASS_OPTIONS
from app.services.scoring.overwatch import OVERWATCH_ROLE_OPTIONS
from app.services.scoring.r6 import R6_ROLE_OPTIONS
from app.services.scoring.registry import SCORERS
from app.services.scoring.rocket_league import ROCKET_LEAGUE_ROLE_OPTIONS
from app.services.scoring.valorant import VAL_ROLE_OPTIONS

SEED_EMAIL_DOMAIN = "seed.auesports.dev"
DEFAULT_PER_GAME = 30
DEFAULT_MAX_TOTAL = 400

STATUS_ORDER = list(RECRUIT_REVIEW_STATUSES)
STATUS_WEIGHTS = {
    "REJECTED": 0.45,
    "WATCHLIST": 0.20,
    "TRYOUT": 0.12,
    "CONTACTED": 0.08,
    "REVIEWED": 0.07,
    "ACCEPTED": 0.05,
    "NEW": 0.03,
}

STATUS_MINIMUMS = {
    "REJECTED": 6,
    "WATCHLIST": 3,
    "TRYOUT": 2,
    "ACCEPTED": 1,
    "CONTACTED": 1,
    "REVIEWED": 1,
    "NEW": 1,
}

FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Riley",
    "Skyler",
    "Quinn",
    "Morgan",
    "Casey",
    "Dakota",
    "Parker",
    "Harper",
    "Cameron",
    "Jules",
    "Avery",
    "Elliot",
    "Reese",
]
LAST_NAMES = [
    "Nguyen",
    "Patel",
    "Johnson",
    "Lopez",
    "Kim",
    "Davis",
    "Brown",
    "Garcia",
    "Wright",
    "Miller",
    "Wilson",
    "Thomas",
    "Anderson",
    "Martinez",
    "Harris",
    "Clark",
]
SCHOOLS = [
    "Auburn High School",
    "Auburn University",
    "Auburn Online Program",
    "Auburn Engineering Co-op",
    "Auburn Community College",
    "Lee-Scott Academy",
    "Opelika High School",
]
CITY_STATES = [
    "Auburn, AL",
    "Opelika, AL",
    "Birmingham, AL",
    "Atlanta, GA",
    "Nashville, TN",
    "Charlotte, NC",
    "Jacksonville, FL",
    "Huntsville, AL",
]
TOURNAMENT_LEVELS = ("none", "local", "regional", "national")
FORTNITE_MODES = ("Solos", "Duos", "Trios", "Squads")
CARD_FORMATS = ("Standard", "Wild")
OTHER_CARD_GAMES = (
    "Magic Arena",
    "Marvel Snap",
    "Legends of Runeterra",
    "Yu-Gi-Oh! Master Duel",
)
SMASH_CHARACTERS = (
    "Pyra/Mythra",
    "Cloud",
    "Steve",
    "Joker",
    "Roy",
    "Wolf",
    "Peach",
    "Pikachu",
    "Sonic",
    "R.O.B.",
)
MARIO_TITLES = ("MK8 Deluxe", "MK8D + Booster Course")
CONTROLLER_TYPES = ("Pro Controller", "GameCube", "Joy-Con", "Wheel")
PLAYSTYLES = ("Aggressive", "Adaptive", "Defensive", "Consistency-focused")
TRACKS = (
    "Big Blue",
    "Waluigi Stadium",
    "Mute City",
    "Mount Wario",
    "Yoshi Circuit",
    "Rainbow Road",
)
NOTE_PHRASES = (
    "Strong comms, wants team structure.",
    "Mechanically solid but inconsistent availability.",
    "Positive attitude, coachable in review.",
    "Needs better VOD discipline.",
    "Good tournament mindset in clutch rounds.",
    "Profile has mixed signals, monitor progress.",
)
LABEL_REASONS = {
    "REJECTED": [
        "Insufficient rank and low availability.",
        "Needs development before team tryouts.",
        "Profile completeness and experience below target.",
    ],
    "WATCHLIST": [
        "Potential upside with additional consistency.",
        "Strong partial indicators, monitor next season.",
        "Worth following after updated competitive results.",
    ],
    "TRYOUT": [
        "Invite to evaluate team fit and comms.",
        "Sufficient score and availability for tryout.",
        "Good upside, verify consistency in scrims.",
    ],
    "ACCEPTED": [
        "Consistent top-tier profile and reliable schedule.",
        "Strong rank, experience, and fit with roster needs.",
        "Immediate impact candidate with proven results.",
    ],
    "CONTACTED": [
        "Reached out for additional details and VODs.",
        "Candidate meets baseline, pending follow-up.",
        "Contacted to confirm role flexibility and schedule.",
    ],
    "REVIEWED": [
        "Initial evaluation completed.",
        "Reviewed profile, waiting for updates.",
        "Scouting notes captured for follow-up.",
    ],
    "NEW": [
        "Application recently submitted.",
        "Awaiting first coach review.",
        "Queued for triage pass.",
    ],
}

GAME_STYLE = {
    "valorant": {"mean": 0.56, "spread": 0.18},
    "cs2": {"mean": 0.52, "spread": 0.20},
    "fortnite": {"mean": 0.50, "spread": 0.22},
    "r6": {"mean": 0.48, "spread": 0.19},
    "rocket-league": {"mean": 0.58, "spread": 0.17},
    "overwatch": {"mean": 0.53, "spread": 0.18},
    "cod": {"mean": 0.47, "spread": 0.21},
    "hearthstone": {"mean": 0.61, "spread": 0.22},
    "smash": {"mean": 0.45, "spread": 0.24},
    "mario-kart": {"mean": 0.55, "spread": 0.19},
}

ROLE_OPTIONS = {
    "valorant": sorted(VAL_ROLE_OPTIONS),
    "cs2": sorted(CS2_ROLE_OPTIONS),
    "fortnite": sorted(FORTNITE_ROLE_OPTIONS),
    "r6": sorted(R6_ROLE_OPTIONS),
    "rocket-league": sorted(ROCKET_LEAGUE_ROLE_OPTIONS),
    "overwatch": sorted(OVERWATCH_ROLE_OPTIONS),
    "cod": sorted(COD_ROLE_OPTIONS),
    "hearthstone": sorted(HEARTHSTONE_CLASS_OPTIONS),
}

RANK_OPTIONS = {
    "valorant": [
        "Iron 1",
        "Iron 3",
        "Bronze 2",
        "Silver 1",
        "Silver 3",
        "Gold 2",
        "Platinum 1",
        "Platinum 3",
        "Diamond 2",
        "Ascendant 1",
        "Ascendant 3",
        "Immortal 2",
        "Radiant",
    ],
    "fortnite": [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Elite",
        "Champion",
        "Unreal",
    ],
    "r6": [
        "Copper",
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Emerald",
        "Diamond",
        "Champion",
    ],
    "rocket-league": [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Champion",
        "Grand Champion",
        "Supersonic Legend",
    ],
    "overwatch": [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Master",
        "Grandmaster",
        "Top 500",
    ],
    "cod": [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Crimson",
        "Iridescent",
        "Top 250",
    ],
}

CS2_LABELS = [
    "Silver 2",
    "Silver Elite",
    "Gold Nova 1",
    "Gold Nova Master",
    "Master Guardian 2",
    "MGE",
    "DMG",
    "LEM",
    "Supreme",
    "Global Elite",
]


@dataclass
class Candidate:
    game_slug: str
    payload: RecruitApplyInput
    score: float
    scoring_result: Any
    city_state: str | None
    created_at: datetime
    status: str = "NEW"


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def now_utc_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def weighted_choice(rng: random.Random, choices: list[tuple[Any, float]]) -> Any:
    total = sum(weight for _, weight in choices if weight > 0)
    if total <= 0:
        return choices[0][0]
    pick = rng.random() * total
    cursor = 0.0
    for item, weight in choices:
        if weight <= 0:
            continue
        cursor += weight
        if pick <= cursor:
            return item
    return choices[-1][0]


def score_to_bucket(skill: float) -> str:
    if skill >= 0.90:
        return "standout"
    if skill >= 0.68:
        return "strong"
    if skill >= 0.45:
        return "average"
    if skill >= 0.22:
        return "weak"
    return "struggling"


def make_skill(game_slug: str, rng: random.Random) -> tuple[float, float, float, bool]:
    style = GAME_STYLE.get(game_slug, {"mean": 0.50, "spread": 0.20})
    archetype = weighted_choice(
        rng,
        [
            ("standout", 0.08),
            ("strong", 0.30),
            ("average", 0.40),
            ("weak", 0.17),
            ("inconsistent", 0.05),
        ],
    )
    base = clamp(rng.gauss(style["mean"], style["spread"]), 0.03, 0.98)
    commitment = clamp(rng.gauss(0.58, 0.24), 0.05, 1.0)
    completeness = clamp(rng.gauss(0.60, 0.25), 0.03, 1.0)
    inconsistent = False

    if archetype == "standout":
        base = clamp(rng.uniform(0.88, 0.99), 0.03, 0.99)
        commitment = clamp(rng.uniform(0.70, 1.0), 0.05, 1.0)
        completeness = clamp(rng.uniform(0.70, 1.0), 0.03, 1.0)
    elif archetype == "strong":
        base = clamp(base + rng.uniform(0.08, 0.18), 0.03, 0.98)
    elif archetype == "weak":
        base = clamp(base - rng.uniform(0.12, 0.28), 0.03, 0.98)
        completeness = clamp(completeness - rng.uniform(0.05, 0.20), 0.03, 1.0)
    elif archetype == "struggling":
        base = clamp(base - rng.uniform(0.18, 0.34), 0.03, 0.98)
    elif archetype == "inconsistent":
        inconsistent = True
        if rng.random() < 0.5:
            base = clamp(base + rng.uniform(0.20, 0.35), 0.03, 0.98)
            commitment = clamp(commitment - rng.uniform(0.22, 0.38), 0.05, 1.0)
            completeness = clamp(completeness - rng.uniform(0.20, 0.32), 0.03, 1.0)
        else:
            base = clamp(base - rng.uniform(0.15, 0.28), 0.03, 0.98)
            commitment = clamp(commitment + rng.uniform(0.24, 0.40), 0.05, 1.0)
            completeness = clamp(completeness + rng.uniform(0.20, 0.30), 0.03, 1.0)

    return base, commitment, completeness, inconsistent


def make_name(rng: random.Random, game_slug: str, idx: int) -> tuple[str, str]:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    if idx % 11 == 0:
        first = f"{first}-{game_slug[:2].upper()}"
    return first[:50], last[:50]


def build_rank_label(
    game_slug: str,
    skill: float,
    rng: random.Random,
    allow_unknown: bool,
) -> str:
    if allow_unknown and rng.random() < 0.08:
        return "Unrated"

    if game_slug == "cs2":
        if rng.random() < 0.45:
            rating = int(clamp((skill + rng.uniform(-0.10, 0.10)) * 30000, 1500, 30000))
            return f"Premier {rating}"
        if rng.random() < 0.35:
            level = int(clamp((skill + rng.uniform(-0.12, 0.10)) * 10, 1, 10))
            return f"FACEIT {level}"
        index = int(clamp(round(skill * (len(CS2_LABELS) - 1)), 0, len(CS2_LABELS) - 1))
        return CS2_LABELS[index]

    labels = RANK_OPTIONS.get(game_slug)
    if not labels:
        return "Unranked"
    index = int(clamp(round(skill * (len(labels) - 1)), 0, len(labels) - 1))
    return labels[index]


def build_hearthstone_rank(skill: float, rng: random.Random, allow_unknown: bool) -> str:
    if allow_unknown and rng.random() < 0.08:
        return "Unranked"
    if skill > 0.93:
        return "Legend"
    tiers = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
    tier_idx = int(clamp(round(skill * (len(tiers) - 1)), 0, len(tiers) - 1))
    division = int(clamp(round((1.0 - skill) * 9 + rng.uniform(-1.8, 1.8)), 1, 10))
    return f"{tiers[tier_idx]} {division}"


def maybe_peak_rank(current_rank: str, game_slug: str, skill: float, rng: random.Random) -> str | None:
    if rng.random() < 0.24:
        return None
    if game_slug == "hearthstone":
        bonus = clamp(skill + rng.uniform(0.02, 0.16), 0.0, 0.99)
        return build_hearthstone_rank(bonus, rng, allow_unknown=False)
    if game_slug == "cs2":
        if current_rank.lower().startswith("premier "):
            current_value = int(current_rank.split(" ", 1)[1])
            boosted = int(clamp(current_value + rng.randint(250, 2400), 1000, 30000))
            return f"Premier {boosted}"
        if current_rank.lower().startswith("faceit "):
            current_value = int(current_rank.split(" ", 1)[1])
            boosted = int(clamp(current_value + rng.randint(1, 3), 1, 10))
            return f"FACEIT {boosted}"
        idx = CS2_LABELS.index(current_rank) if current_rank in CS2_LABELS else 0
        idx = int(clamp(idx + rng.randint(0, 2), 0, len(CS2_LABELS) - 1))
        return CS2_LABELS[idx]
    if game_slug in RANK_OPTIONS and current_rank in RANK_OPTIONS[game_slug]:
        labels = RANK_OPTIONS[game_slug]
        idx = labels.index(current_rank)
        boosted_idx = int(clamp(idx + rng.randint(0, 2), 0, len(labels) - 1))
        return labels[boosted_idx]
    return current_rank


def pick_tournament_level(skill: float, rng: random.Random, inconsistent: bool) -> str:
    weights = {
        "none": 0.10 + (0.55 * (1.0 - skill)),
        "local": 0.30 + (0.16 * (1.0 - abs(skill - 0.50))),
        "regional": 0.15 + (0.35 * skill),
        "national": 0.02 + (0.20 * skill),
    }
    if inconsistent:
        weights["none"] += 0.08
        weights["national"] += 0.03
    return weighted_choice(rng, [(level, weights[level]) for level in TOURNAMENT_LEVELS])


def make_profile_and_availability(
    game_slug: str,
    idx: int,
    rng: random.Random,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    skill, commitment, completeness, inconsistent = make_skill(game_slug, rng)
    first, last = make_name(rng, game_slug, idx)
    grad_year = now_utc_naive().year + rng.randint(0, 6)
    if rng.random() < 0.12:
        grad_year = None

    school = rng.choice(SCHOOLS) if rng.random() > 0.10 else None
    city_state = rng.choice(CITY_STATES) if rng.random() > 0.22 else None
    preferred_contact = weighted_choice(
        rng,
        [("discord", 0.55), ("email", 0.35), (None, 0.10)],
    )

    hours = int(clamp(round(2 + commitment * 18 + rng.gauss(0, 2.6)), 1, 40))
    weeknights = rng.random() < clamp(0.22 + (commitment * 0.70), 0.05, 0.95)
    weekends = rng.random() < clamp(0.30 + (commitment * 0.65), 0.10, 0.98)
    if inconsistent and rng.random() < 0.45:
        weeknights = not weeknights
    if inconsistent and rng.random() < 0.35:
        weekends = not weekends

    tracker_present = rng.random() < clamp(0.30 + (completeness * 0.65), 0.08, 0.98)
    role_present = rng.random() > 0.05
    peak_present = rng.random() < clamp(0.36 + (completeness * 0.45), 0.10, 0.95)

    team_experience = rng.random() < clamp(0.12 + (skill * 0.60) + (commitment * 0.15), 0.05, 0.95)
    scrim_experience = rng.random() < clamp(0.10 + (skill * 0.58) + (commitment * 0.20), 0.05, 0.95)
    tournament_experience = pick_tournament_level(skill, rng, inconsistent)

    ign = f"{first.lower()}{last.lower()}{rng.randint(10, 9999)}"
    discord = f"{first.lower()}_{last.lower()}#{rng.randint(1000, 9999)}"
    email = f"{game_slug}-{idx:03d}-{rng.randint(100, 999)}@{SEED_EMAIL_DOMAIN}"

    current_rank_label: str | None = None
    peak_rank_label: str | None = None
    primary_role: str | None = None
    secondary_role: str | None = None

    if game_slug == "hearthstone":
        current_rank_label = build_hearthstone_rank(skill, rng, allow_unknown=True)
        if peak_present:
            peak_rank_label = maybe_peak_rank(current_rank_label, game_slug, skill, rng)
        if role_present:
            primary_role = rng.choice(ROLE_OPTIONS["hearthstone"])
        if rng.random() < 0.55:
            secondary_role = rng.choice(ROLE_OPTIONS["hearthstone"])
    elif game_slug not in {"smash", "mario-kart"}:
        current_rank_label = build_rank_label(game_slug, skill, rng, allow_unknown=True)
        if peak_present:
            peak_rank_label = maybe_peak_rank(current_rank_label, game_slug, skill, rng)
        roles = ROLE_OPTIONS.get(game_slug, ["Flex"])
        if role_present:
            primary_role = rng.choice(roles)
        if rng.random() < 0.62:
            secondary_role = rng.choice(roles)

    profile: dict[str, Any] = {
        "ign": ign if game_slug != "smash" or rng.random() > 0.18 else None,
        "current_rank_label": current_rank_label,
        "peak_rank_label": peak_rank_label,
        "primary_role": primary_role,
        "secondary_role": secondary_role,
        "tracker_url": (
            f"https://tracker.gg/{game_slug}/profile/{ign}"
            if tracker_present
            else None
        ),
        "team_experience": team_experience,
        "scrim_experience": scrim_experience,
        "tournament_experience": tournament_experience,
        "fortnite_mode": rng.choice(FORTNITE_MODES) if game_slug == "fortnite" else None,
        "ranked_wins": None,
        "years_played": None,
        "legend_peak_rank": None,
        "preferred_format": None,
        "other_card_games": None,
        "gsp": None,
        "regional_rank": None,
        "best_wins": None,
        "characters": None,
        "lounge_rating": None,
        "preferred_title": None,
        "controller_type": None,
        "playstyle": None,
        "preferred_tracks": None,
    }

    if game_slug == "hearthstone":
        profile["ranked_wins"] = int(clamp(round((skill**1.1) * 4600 + rng.gauss(0, 280)), 0, 5000))
        profile["years_played"] = int(clamp(round(skill * 8 + rng.uniform(0, 3)), 0, 12))
        if rng.random() < clamp(0.15 + skill * 0.45, 0.10, 0.80):
            profile["legend_peak_rank"] = int(clamp(round((1.0 - skill) * 4200 + rng.uniform(1, 400)), 1, 50000))
        profile["preferred_format"] = rng.choice(CARD_FORMATS) if rng.random() > 0.12 else None
        if rng.random() > 0.35:
            choices = rng.sample(OTHER_CARD_GAMES, k=rng.randint(1, 2))
            profile["other_card_games"] = ", ".join(choices)
        if rng.random() < 0.10:
            profile["tracker_url"] = None

    if game_slug == "smash":
        gsp_val = int(clamp(round(2_000_000 + (skill * 13_600_000) + rng.gauss(0, 850_000)), 50_000, 16_000_000))
        profile["gsp"] = gsp_val if rng.random() > 0.08 else None
        regional_options = ["Top 10", "Top 25", "Top 50", "Top 100", "Honorable Mention"]
        profile["regional_rank"] = rng.choice(regional_options) if rng.random() < clamp(0.22 + skill * 0.60, 0.08, 0.92) else None
        if rng.random() < clamp(0.18 + skill * 0.62, 0.08, 0.96):
            wins_count = rng.randint(1, 6 if skill > 0.75 else 4)
            wins = [f"P{rng.randint(5, 250)}" for _ in range(wins_count)]
            profile["best_wins"] = ", ".join(wins)
        if rng.random() < clamp(0.30 + skill * 0.60, 0.10, 0.95):
            chars = rng.sample(SMASH_CHARACTERS, k=rng.randint(1, 3))
            profile["characters"] = ", ".join(chars)
        if rng.random() < 0.25:
            profile["tracker_url"] = None
        profile["primary_role"] = None
        profile["secondary_role"] = None
        profile["current_rank_label"] = None
        profile["peak_rank_label"] = None

    if game_slug == "mario-kart":
        lounge = int(clamp(round(1100 + (skill * 8200) + rng.gauss(0, 450)), 300, 10000))
        profile["lounge_rating"] = lounge if rng.random() > 0.06 else None
        profile["preferred_title"] = rng.choice(MARIO_TITLES) if rng.random() > 0.12 else None
        profile["controller_type"] = rng.choice(CONTROLLER_TYPES) if rng.random() > 0.14 else None
        profile["playstyle"] = rng.choice(PLAYSTYLES) if rng.random() > 0.10 else None
        if rng.random() < 0.70:
            chosen_tracks = rng.sample(TRACKS, k=rng.randint(1, 3))
            profile["preferred_tracks"] = ", ".join(chosen_tracks)
        if rng.random() < 0.20:
            profile["tracker_url"] = None
        profile["primary_role"] = None
        profile["secondary_role"] = None
        profile["current_rank_label"] = None
        profile["peak_rank_label"] = None

    if game_slug not in {"smash", "mario-kart"}:
        if not profile["primary_role"]:
            roles = ROLE_OPTIONS.get(game_slug, ["Flex"])
            profile["primary_role"] = rng.choice(roles)
        if rng.random() < 0.14:
            profile["secondary_role"] = None

    if game_slug not in {"smash", "mario-kart"} and rng.random() < 0.06:
        profile["tracker_url"] = None
        profile["secondary_role"] = None
        profile["peak_rank_label"] = None

    school_choice = school
    if score_to_bucket(skill) in {"standout", "strong"} and rng.random() < 0.08:
        school_choice = None

    payload_dict = {
        "first_name": first,
        "last_name": last,
        "email": email,
        "discord": discord[:50],
        "current_school": school_choice,
        "graduation_year": grad_year,
        "preferred_contact": preferred_contact,
        "availability": {
            "hours_per_week": hours,
            "weeknights_available": weeknights,
            "weekends_available": weekends,
        },
        "game_slug": game_slug,
        "profile": profile,
    }
    return payload_dict, {"city_state": city_state}, score_to_bucket(skill)


def build_status_targets(total: int, rng: random.Random) -> dict[str, int]:
    targets: dict[str, int] = {}
    for status in STATUS_ORDER:
        minimum = STATUS_MINIMUMS.get(status, 1)
        weighted = int(round(total * STATUS_WEIGHTS.get(status, 0.01)))
        targets[status] = max(minimum, weighted)

    while sum(targets.values()) > total:
        reducible = [
            status
            for status in STATUS_ORDER
            if targets[status] > STATUS_MINIMUMS.get(status, 1)
        ]
        if not reducible:
            break
        status = max(reducible, key=lambda s: targets[s] - STATUS_MINIMUMS.get(s, 1))
        targets[status] -= 1

    while sum(targets.values()) < total:
        status = weighted_choice(rng, [(s, STATUS_WEIGHTS.get(s, 0.01)) for s in STATUS_ORDER])
        targets[status] += 1

    return targets


def status_desirability(status: str, quantile: float) -> float:
    if status == "ACCEPTED":
        return 0.06 + (quantile**2.4) * 1.85
    if status == "TRYOUT":
        return 0.10 + max(0.0, 1.0 - abs(quantile - 0.80) * 3.0)
    if status == "WATCHLIST":
        return 0.12 + max(0.0, 1.0 - abs(quantile - 0.63) * 2.2)
    if status == "CONTACTED":
        return 0.10 + max(0.0, 1.0 - abs(quantile - 0.52) * 2.4)
    if status == "REVIEWED":
        return 0.09 + max(0.0, 1.0 - abs(quantile - 0.40) * 2.7)
    if status == "NEW":
        return 0.08 + max(0.0, 1.0 - abs(quantile - 0.28) * 3.0)
    if status == "REJECTED":
        return 0.05 + ((1.0 - quantile) ** 2.1) * 1.9
    return 0.1


def assign_statuses(candidates: list[Candidate], rng: random.Random) -> Counter[str]:
    targets = build_status_targets(len(candidates), rng)
    sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
    total = len(sorted_candidates)

    for idx, candidate in enumerate(sorted_candidates):
        quantile = 1.0 if total == 1 else 1.0 - (idx / (total - 1))
        choices: list[tuple[str, float]] = []
        for status in STATUS_ORDER:
            remaining = targets.get(status, 0)
            if remaining <= 0:
                continue
            desirability = status_desirability(status, quantile)
            noise = rng.uniform(0.82, 1.22)
            choices.append((status, remaining * desirability * noise))
        chosen = weighted_choice(rng, choices)
        candidate.status = chosen
        targets[chosen] -= 1

    return Counter(candidate.status for candidate in candidates)


def purge_previous_seed_data(db: Session) -> int:
    marker = f"%@{SEED_EMAIL_DOMAIN}"
    seeded_ids = [
        app_id
        for (app_id,) in db.query(RecruitApplication.id)
        .filter(RecruitApplication.email.like(marker))
        .all()
    ]
    if not seeded_ids:
        return 0

    db.query(RecruitReview).filter(RecruitReview.application_id.in_(seeded_ids)).delete(
        synchronize_session=False
    )
    db.query(RecruitRanking).filter(RecruitRanking.application_id.in_(seeded_ids)).delete(
        synchronize_session=False
    )
    db.query(RecruitGameProfile).filter(
        RecruitGameProfile.application_id.in_(seeded_ids)
    ).delete(synchronize_session=False)
    db.query(RecruitAvailability).filter(
        RecruitAvailability.application_id.in_(seeded_ids)
    ).delete(synchronize_session=False)
    db.query(RecruitApplication).filter(RecruitApplication.id.in_(seeded_ids)).delete(
        synchronize_session=False
    )
    return len(seeded_ids)


def review_note(rng: random.Random, bucket: str, status: str) -> str | None:
    if status == "NEW":
        return rng.choice(NOTE_PHRASES) if rng.random() < 0.22 else None
    if rng.random() < 0.35:
        return None
    bucket_prefix = {
        "standout": "Standout profile.",
        "strong": "Above-average profile.",
        "average": "Mid-tier profile.",
        "weak": "Below-target profile.",
        "struggling": "High-risk profile.",
    }.get(bucket, "Mixed profile.")
    return f"{bucket_prefix} {rng.choice(NOTE_PHRASES)}"


def create_review(
    db: Session,
    candidate: Candidate,
    app_id: int,
    reviewer_ids: list[int],
    rng: random.Random,
    bucket: str,
) -> RecruitReview:
    status = candidate.status
    has_label = status != "NEW" or rng.random() < 0.30
    labeled_at = None
    if has_label:
        labeled_at = candidate.created_at + timedelta(hours=rng.randint(2, 240))
    reason = None
    if has_label:
        reason = rng.choice(LABEL_REASONS.get(status, LABEL_REASONS["REVIEWED"]))

    review = RecruitReview(
        application_id=app_id,
        status=status,
        reviewer_user_id=rng.choice(reviewer_ids) if reviewer_ids and has_label else None,
        labeled_at=labeled_at,
        label_reason=reason,
        notes=review_note(rng, bucket, status),
        updated_at=labeled_at or candidate.created_at,
    )
    db.add(review)
    return review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dev-only recruit seed utility. Creates realistic RecruitApplication/"
            "Availability/GameProfile/Ranking/Review test data across all supported games."
        )
    )
    parser.add_argument(
        "--per-game",
        type=int,
        default=DEFAULT_PER_GAME,
        help=f"Target recruits per supported game (default: {DEFAULT_PER_GAME}).",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=DEFAULT_MAX_TOTAL,
        help=f"Maximum total recruits before auto-scaling per-game volume (default: {DEFAULT_MAX_TOTAL}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible output (default: 42).",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Append to existing seed data. By default, previously generated test recruits "
            f"with email domain @{SEED_EMAIL_DOMAIN} are removed first."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    db = SessionLocal()

    try:
        games = db.query(Game).order_by(Game.slug.asc()).all()
        supported_games = [game for game in games if game.slug in SCORERS]
        unsupported = [game.slug for game in games if game.slug not in SCORERS]

        if not supported_games:
            print("No supported games found in DB. Seed games first (python seed.py).")
            return 1

        per_game = max(1, args.per_game)
        max_total = max(1, args.max_total)
        total_requested = per_game * len(supported_games)
        if total_requested > max_total:
            per_game = max(1, max_total // len(supported_games))
            print(
                f"Requested total {total_requested} exceeds --max-total {max_total}. "
                f"Auto-adjusting to {per_game} per game."
            )

        if not args.append:
            removed = purge_previous_seed_data(db)
            if removed:
                print(f"Removed {removed} previously seeded test recruit applications.")

        reviewer_ids = [uid for (uid,) in db.query(AdminUser.id).all()]

        created_by_game: Counter[str] = Counter()
        statuses_by_game: dict[str, Counter[str]] = {}
        total_created = 0

        for game in supported_games:
            candidates: list[Candidate] = []
            quality_buckets: dict[int, str] = {}
            for idx in range(per_game):
                payload_dict, extra, bucket = make_profile_and_availability(game.slug, idx, rng)
                payload = RecruitApplyInput.model_validate(payload_dict)
                result = score_application(game.slug, payload)
                created_at = now_utc_naive() - timedelta(
                    days=rng.randint(1, 210),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                candidate = Candidate(
                    game_slug=game.slug,
                    payload=payload,
                    score=result.score,
                    scoring_result=result,
                    city_state=extra["city_state"],
                    created_at=created_at,
                )
                candidates.append(candidate)
                quality_buckets[idx] = bucket

            statuses_by_game[game.slug] = assign_statuses(candidates, rng)

            for idx, candidate in enumerate(candidates):
                payload = candidate.payload
                result = candidate.scoring_result

                app_obj = RecruitApplication(
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                    email=payload.email,
                    discord=payload.discord,
                    current_school=payload.current_school,
                    city_state=candidate.city_state,
                    graduation_year=payload.graduation_year,
                    preferred_contact=payload.preferred_contact,
                    created_at=candidate.created_at,
                )
                db.add(app_obj)
                db.flush()

                availability = RecruitAvailability(
                    application_id=app_obj.id,
                    hours_per_week=payload.availability.hours_per_week,
                    weeknights_available=payload.availability.weeknights_available,
                    weekends_available=payload.availability.weekends_available,
                )
                db.add(availability)

                profile = RecruitGameProfile(
                    application_id=app_obj.id,
                    game_id=game.id,
                    ign=payload.profile.ign,
                    fortnite_mode=payload.profile.fortnite_mode,
                    ranked_wins=payload.profile.ranked_wins,
                    years_played=payload.profile.years_played,
                    legend_peak_rank=payload.profile.legend_peak_rank,
                    preferred_format=payload.profile.preferred_format,
                    other_card_games=payload.profile.other_card_games,
                    gsp=payload.profile.gsp,
                    regional_rank=payload.profile.regional_rank,
                    best_wins=payload.profile.best_wins,
                    characters=payload.profile.characters,
                    lounge_rating=payload.profile.lounge_rating,
                    preferred_title=payload.profile.preferred_title,
                    controller_type=payload.profile.controller_type,
                    playstyle=payload.profile.playstyle,
                    preferred_tracks=payload.profile.preferred_tracks,
                    current_rank_label=payload.profile.current_rank_label,
                    current_rank_numeric=result.current_rank_numeric,
                    peak_rank_label=payload.profile.peak_rank_label,
                    peak_rank_numeric=result.peak_rank_numeric,
                    primary_role=payload.profile.primary_role,
                    secondary_role=payload.profile.secondary_role,
                    tracker_url=payload.profile.tracker_url,
                    team_experience=payload.profile.team_experience,
                    scrim_experience=payload.profile.scrim_experience,
                    tournament_experience=payload.profile.tournament_experience,
                    created_at=candidate.created_at,
                )
                db.add(profile)

                ranking = RecruitRanking(
                    application_id=app_obj.id,
                    game_id=game.id,
                    score=result.score,
                    explanation_json=result.explanation,
                    model_version=result.model_version,
                    raw_inputs_json=result.raw_inputs,
                    normalized_features_json=result.normalized_features,
                    scoring_method=result.scoring_method,
                    is_current=True,
                    scored_at=candidate.created_at,
                    created_at=candidate.created_at,
                )
                db.add(ranking)

                create_review(
                    db=db,
                    candidate=candidate,
                    app_id=app_obj.id,
                    reviewer_ids=reviewer_ids,
                    rng=rng,
                    bucket=quality_buckets[idx],
                )
                created_by_game[game.slug] += 1
                total_created += 1

        db.commit()

        print("")
        print("Seed summary")
        print("-----------")
        if unsupported:
            print(f"Skipped games not in scoring registry: {', '.join(sorted(unsupported))}")
        for game in supported_games:
            status_counts = statuses_by_game.get(game.slug, Counter())
            print(
                f"{game.slug}: created={created_by_game[game.slug]} "
                f"status_counts={dict(status_counts)}"
            )
        aggregate = Counter()
        for counter in statuses_by_game.values():
            aggregate.update(counter)
        print(f"total_created={total_created}")
        print(f"aggregate_status_counts={dict(aggregate)}")
        print("")
        print(
            f"Seed marker: all generated emails end with @{SEED_EMAIL_DOMAIN} "
            "(used for safe cleanup on rerun when --append is not set)."
        )

        return 0
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
