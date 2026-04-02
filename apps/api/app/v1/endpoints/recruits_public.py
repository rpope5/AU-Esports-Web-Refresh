from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import SessionLocal
from app.schemas.recruit import RecruitApplyInput
from app.models.recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
)
from app.models.game import Game
from app.services.scoring.base import score_application


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

    try:
        scoring_result = score_application(data.game_slug, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Create game profile
    profile = RecruitGameProfile(
        application_id=app_obj.id,
        game_id=game.id,
        ign=data.profile.ign,
        current_rank_label=data.profile.current_rank_label,
        current_rank_numeric=scoring_result.current_rank_numeric,
        peak_rank_label=data.profile.peak_rank_label,
        peak_rank_numeric=scoring_result.peak_rank_numeric,
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
        lounge_rating=data.profile.lounge_rating,
        preferred_title=data.profile.preferred_title,
        controller_type=data.profile.controller_type,
        playstyle=data.profile.playstyle,
        preferred_tracks=data.profile.preferred_tracks,
    )

    db.add(profile)
    db.commit()

    (
        db.query(RecruitRanking)
        .filter(
            RecruitRanking.application_id == app_obj.id,
            RecruitRanking.game_id == game.id,
            RecruitRanking.is_current.is_(True),
        )
        .update({"is_current": False}, synchronize_session=False)
    )

    # Save ranking
    ranking = RecruitRanking(
        application_id=app_obj.id,
        game_id=game.id,
        score=scoring_result.score,
        explanation_json=scoring_result.explanation,
        model_version=scoring_result.model_version,
        raw_inputs_json=scoring_result.raw_inputs,
        normalized_features_json=scoring_result.normalized_features,
        scoring_method=scoring_result.scoring_method,
        is_current=True,
        scored_at=datetime.utcnow(),
    )

    db.add(ranking)
    db.commit()

    return {
        "message": "Application submitted",
        "game": data.game_slug,
        "score": scoring_result.score,
        "explanation": scoring_result.explanation,
    }
