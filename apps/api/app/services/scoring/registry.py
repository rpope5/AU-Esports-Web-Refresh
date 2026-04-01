from dataclasses import dataclass
from typing import Any, Callable

from app.services.scoring.valorant import (
    score_valorant,
    valorant_rank_to_numeric,
    ValorantInputs,
)
from app.services.scoring.cs2 import (
    score_cs2,
    cs2_rank_to_numeric,
    CS2Inputs,
)
from app.services.scoring.fortnite import (
    score_fortnite,
    fortnite_rank_to_numeric,
    FortniteInputs,
)
from app.services.scoring.r6 import (
    score_r6,
    r6_rank_to_numeric,
    R6Inputs,
)
from app.services.scoring.rocket_league import (
    score_rocket_league,
    rocket_league_rank_to_numeric,
    RocketLeagueInputs,
)
from app.services.scoring.overwatch import (
    score_overwatch,
    overwatch_rank_to_numeric,
    OverwatchInputs,
)
from app.services.scoring.cod import (
    score_cod,
    cod_rank_to_numeric,
    CODInputs,
)
from app.services.scoring.hearthstone import (
    score_hearthstone,
    hearthstone_rank_to_numeric,
    HearthstoneInputs,
)
from app.services.scoring.smash import score_smash, SmashInputs
from app.services.scoring.mario_kart import score_mario_kart, MarioKartInputs


ScorerFn = Callable[[Any], tuple[float, dict]]
PrepareFn = Callable[[Any], "PreparedScoringInput"]


@dataclass
class PreparedScoringInput:
    scorer_inputs: Any
    current_rank_numeric: float | None
    peak_rank_numeric: float | None
    raw_inputs: dict[str, Any]
    normalized_features: dict[str, Any]


@dataclass
class ScorerConfig:
    scorer: ScorerFn
    prepare: PrepareFn
    model_version: str


def _prepare_standard_ranked(payload: Any, rank_to_numeric: Callable[[str], float], inputs_cls: type) -> PreparedScoringInput:
    current_rank_numeric = rank_to_numeric(payload.profile.current_rank_label)
    peak_rank_numeric = (
        rank_to_numeric(payload.profile.peak_rank_label)
        if payload.profile.peak_rank_label
        else None
    )

    scorer_inputs = inputs_cls(
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
    )

    return PreparedScoringInput(
        scorer_inputs=scorer_inputs,
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=peak_rank_numeric,
        raw_inputs={
            "current_rank_label": payload.profile.current_rank_label,
            "peak_rank_label": payload.profile.peak_rank_label,
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
        normalized_features={},
    )


def _prepare_valorant(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, valorant_rank_to_numeric, ValorantInputs)


def _prepare_cs2(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, cs2_rank_to_numeric, CS2Inputs)


def _prepare_fortnite(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, fortnite_rank_to_numeric, FortniteInputs)


def _prepare_r6(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, r6_rank_to_numeric, R6Inputs)


def _prepare_rocket_league(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, rocket_league_rank_to_numeric, RocketLeagueInputs)


def _prepare_overwatch(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, overwatch_rank_to_numeric, OverwatchInputs)


def _prepare_cod(payload: Any) -> PreparedScoringInput:
    return _prepare_standard_ranked(payload, cod_rank_to_numeric, CODInputs)


def _prepare_hearthstone(payload: Any) -> PreparedScoringInput:
    current_rank_numeric = hearthstone_rank_to_numeric(payload.profile.current_rank_label)
    peak_rank_numeric = (
        hearthstone_rank_to_numeric(payload.profile.peak_rank_label)
        if payload.profile.peak_rank_label
        else None
    )

    scorer_inputs = HearthstoneInputs(
        rank_numeric=current_rank_numeric,
        ranked_wins=payload.profile.ranked_wins or 0,
        years_played=payload.profile.years_played or 0,
        legend_peak_rank=payload.profile.legend_peak_rank,
        hours_per_week=payload.availability.hours_per_week,
        weeknights_available=payload.availability.weeknights_available,
        weekends_available=payload.availability.weekends_available,
        tournament_experience=payload.profile.tournament_experience,
        tracker_url_present=bool(payload.profile.tracker_url),
        ign_present=bool(payload.profile.ign),
        deck_info_present=bool(payload.profile.secondary_role),
    )

    return PreparedScoringInput(
        scorer_inputs=scorer_inputs,
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=peak_rank_numeric,
        raw_inputs={
            "current_rank_label": payload.profile.current_rank_label,
            "peak_rank_label": payload.profile.peak_rank_label,
            "ranked_wins": payload.profile.ranked_wins or 0,
            "years_played": payload.profile.years_played or 0,
            "legend_peak_rank": payload.profile.legend_peak_rank,
            "hours_per_week": payload.availability.hours_per_week,
            "weeknights_available": payload.availability.weeknights_available,
            "weekends_available": payload.availability.weekends_available,
            "tournament_experience": payload.profile.tournament_experience,
            "tracker_url_present": bool(payload.profile.tracker_url),
            "ign_present": bool(payload.profile.ign),
            "deck_info_present": bool(payload.profile.secondary_role),
        },
        normalized_features={},
    )


def _prepare_smash(payload: Any) -> PreparedScoringInput:
    scorer_inputs = SmashInputs(
        gsp=payload.profile.gsp or 0,
        regional_rank=payload.profile.regional_rank,
        best_wins=payload.profile.best_wins,
        hours_per_week=payload.availability.hours_per_week,
        weeknights_available=payload.availability.weeknights_available,
        weekends_available=payload.availability.weekends_available,
        tournament_experience=payload.profile.tournament_experience,
        tracker_url_present=bool(payload.profile.tracker_url),
        characters_present=bool(payload.profile.characters),
    )

    return PreparedScoringInput(
        scorer_inputs=scorer_inputs,
        current_rank_numeric=None,
        peak_rank_numeric=None,
        raw_inputs={
            "gsp": payload.profile.gsp or 0,
            "regional_rank": payload.profile.regional_rank,
            "best_wins": payload.profile.best_wins,
            "hours_per_week": payload.availability.hours_per_week,
            "weeknights_available": payload.availability.weeknights_available,
            "weekends_available": payload.availability.weekends_available,
            "tournament_experience": payload.profile.tournament_experience,
            "tracker_url_present": bool(payload.profile.tracker_url),
            "characters_present": bool(payload.profile.characters),
        },
        normalized_features={},
    )


def _prepare_mario_kart(payload: Any) -> PreparedScoringInput:
    current_rank_numeric = float(payload.profile.lounge_rating or 0)
    scorer_inputs = MarioKartInputs(
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
    )

    return PreparedScoringInput(
        scorer_inputs=scorer_inputs,
        current_rank_numeric=current_rank_numeric,
        peak_rank_numeric=None,
        raw_inputs={
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
        normalized_features={},
    )


SCORERS: dict[str, ScorerConfig] = {
    "valorant": ScorerConfig(
        scorer=score_valorant,
        prepare=_prepare_valorant,
        model_version="v1_valorant",
    ),
    "cs2": ScorerConfig(
        scorer=score_cs2,
        prepare=_prepare_cs2,
        model_version="v1_cs2",
    ),
    "fortnite": ScorerConfig(
        scorer=score_fortnite,
        prepare=_prepare_fortnite,
        model_version="v1_fortnite",
    ),
    "r6": ScorerConfig(
        scorer=score_r6,
        prepare=_prepare_r6,
        model_version="v1_r6",
    ),
    "rocket-league": ScorerConfig(
        scorer=score_rocket_league,
        prepare=_prepare_rocket_league,
        model_version="v1_rocket_league",
    ),
    "overwatch": ScorerConfig(
        scorer=score_overwatch,
        prepare=_prepare_overwatch,
        model_version="v1_overwatch",
    ),
    "cod": ScorerConfig(
        scorer=score_cod,
        prepare=_prepare_cod,
        model_version="v1_cod",
    ),
    "hearthstone": ScorerConfig(
        scorer=score_hearthstone,
        prepare=_prepare_hearthstone,
        model_version="v1_hearthstone",
    ),
    "smash": ScorerConfig(
        scorer=score_smash,
        prepare=_prepare_smash,
        model_version="v1_smash",
    ),
    "mario-kart": ScorerConfig(
        scorer=score_mario_kart,
        prepare=_prepare_mario_kart,
        model_version="v1_mario_kart",
    ),
}
