from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.recruit import RecruitApplyInput
from app.models.recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
)
from app.models.game import Game

from app.services.scoring.valorant import (
    valorant_rank_to_numeric,
    score_valorant,
    ValorantInputs,
)
from app.services.scoring.cs2 import (
    cs2_rank_to_numeric,
    score_cs2,
    CS2Inputs,
)
from app.services.scoring.fortnite import (
    fortnite_rank_to_numeric,
    score_fortnite,
    FortniteInputs,
)
from app.services.scoring.r6 import (
    r6_rank_to_numeric,
    score_r6,
    R6Inputs,
)
from app.services.scoring.rocket_league import (
    rocket_league_rank_to_numeric,
    score_rocket_league,
    RocketLeagueInputs,
)
from app.services.scoring.overwatch import (
    overwatch_rank_to_numeric,
    score_overwatch,
    OverwatchInputs,
)
from app.services.scoring.cod import (
    cod_rank_to_numeric,
    score_cod,
    CODInputs,
)
from app.services.scoring.hearthstone import (
    hearthstone_rank_to_numeric,
    score_hearthstone,
    HearthstoneInputs,
)
from app.services.scoring.smash import (
    score_smash,
    SmashInputs,
)


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/recruit/apply")
def apply_recruit(data: RecruitApplyInput, db: Session = Depends(get_db)):
    # Create application
    app_obj = RecruitApplication(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        discord=data.discord,
        current_school=data.current_school,
        graduation_year=data.graduation_year,
        preferred_contact=data.preferred_contact,
    )

    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)

    # Availability
    avail = RecruitAvailability(
        application_id=app_obj.id,
        hours_per_week=data.availability.hours_per_week,
        weeknights_available=data.availability.weeknights_available,
        weekends_available=data.availability.weekends_available,
    )
    db.add(avail)

    # Get selected game
    game = db.query(Game).filter(Game.slug == data.game_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Game-specific rank parsing + scoring
    rank_numeric = None
    peak_rank_numeric = None
    if data.game_slug == "valorant":
        rank_numeric = valorant_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            valorant_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = ValorantInputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_valorant(inputs)
        model_version = "v1_valorant"

    elif data.game_slug == "cs2":
        rank_numeric = cs2_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            cs2_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = CS2Inputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_cs2(inputs)
        model_version = "v1_cs2"
        
    elif data.game_slug == "fortnite":
        rank_numeric = fortnite_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            fortnite_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = FortniteInputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_fortnite(inputs)
        model_version = "v1_fortnite"
        
    elif data.game_slug == "r6":
        rank_numeric = r6_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            r6_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = R6Inputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_r6(inputs)
        model_version = "v1_r6"
        
    elif data.game_slug == "rocket-league":
        rank_numeric = rocket_league_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            rocket_league_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = RocketLeagueInputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_rocket_league(inputs)
        model_version = "v1_rocket_league"
        
    elif data.game_slug == "overwatch":
        rank_numeric = overwatch_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            overwatch_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = OverwatchInputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_overwatch(inputs)
        model_version = "v1_overwatch"
        
    elif data.game_slug == "cod":
        rank_numeric = cod_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            cod_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = CODInputs(
            rank_numeric=rank_numeric,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            team_experience=data.profile.team_experience,
            scrim_experience=data.profile.scrim_experience,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            roles_present=bool(data.profile.primary_role),
            peak_rank_present=bool(data.profile.peak_rank_label),
        )
        score, explanation = score_cod(inputs)
        model_version = "v1_cod"
        
    elif data.game_slug == "hearthstone":
        rank_numeric = hearthstone_rank_to_numeric(data.profile.current_rank_label)
        peak_rank_numeric = (
            hearthstone_rank_to_numeric(data.profile.peak_rank_label)
            if data.profile.peak_rank_label
            else None
        )

        inputs = HearthstoneInputs(
            rank_numeric=rank_numeric,
            ranked_wins=data.profile.ranked_wins or 0,
            years_played=data.profile.years_played or 0,
            legend_peak_rank=data.profile.legend_peak_rank,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            ign_present=bool(data.profile.ign),
            deck_info_present=bool(data.profile.secondary_role),
        )
        score, explanation = score_hearthstone(inputs)
        model_version = "v1_hearthstone"
        
    elif data.game_slug == "smash":
        inputs = SmashInputs(
            gsp=data.profile.gsp or 0,
            regional_rank=data.profile.regional_rank,
            best_wins=data.profile.best_wins,
            hours_per_week=data.availability.hours_per_week,
            weeknights_available=data.availability.weeknights_available,
            weekends_available=data.availability.weekends_available,
            tournament_experience=data.profile.tournament_experience,
            tracker_url_present=bool(data.profile.tracker_url),
            characters_present=bool(data.profile.characters),
        )
        score, explanation = score_smash(inputs)
        model_version = "v1_smash"

    else:
        raise HTTPException(status_code=400, detail="Unsupported game")

    # Create game profile
    profile = RecruitGameProfile(
        application_id=app_obj.id,
        game_id=game.id,
        ign=data.profile.ign,
        current_rank_label=data.profile.current_rank_label,
        current_rank_numeric=rank_numeric,
        peak_rank_label=data.profile.peak_rank_label,
        peak_rank_numeric=peak_rank_numeric,
        primary_role=data.profile.primary_role,
        secondary_role=data.profile.secondary_role,
        tracker_url=data.profile.tracker_url,
        team_experience=data.profile.team_experience,
        scrim_experience=data.profile.scrim_experience,
        tournament_experience=data.profile.tournament_experience,
        fortnite_mode=data.profile.fortnite_mode,
        ranked_wins=data.profile.ranked_wins,
        years_played=data.profile.years_played,
        legend_peak_rank=data.profile.legend_peak_rank,
        preferred_format=data.profile.preferred_format,
        other_card_games=data.profile.other_card_games,
        gsp=data.profile.gsp,
        regional_rank=data.profile.regional_rank,
        best_wins=data.profile.best_wins,
        characters=data.profile.characters,
    )

    db.add(profile)
    db.commit()

    # Save ranking
    ranking = RecruitRanking(
        application_id=app_obj.id,
        game_id=game.id,
        score=score,
        explanation_json=explanation,
        model_version=model_version,
    )

    db.add(ranking)
    db.commit()

    return {
        "message": "Application submitted",
        "game": data.game_slug,
        "score": score,
        "explanation": explanation,
    }