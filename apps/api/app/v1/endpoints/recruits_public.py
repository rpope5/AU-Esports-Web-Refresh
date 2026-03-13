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