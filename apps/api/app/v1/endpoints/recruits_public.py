from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.recruit import RecruitApplyInput
from app.models.recruit import RecruitApplication, RecruitAvailability, RecruitGameProfile
from app.models.game import Game
from app.services.scoring.valorant import valorant_rank_to_numeric, score_valorant, ValorantInputs
from app.models.recruit import RecruitRanking

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
        preferred_contact=data.preferred_contact
    )

    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)

    # Availability
    avail = RecruitAvailability(
        application_id=app_obj.id,
        hours_per_week=data.availability.hours_per_week,
        weeknights_available=data.availability.weeknights_available,
        weekends_available=data.availability.weekends_available
    )

    db.add(avail)

    # Get game
    game = db.query(Game).filter(Game.slug == "valorant").first()

    rank_numeric = valorant_rank_to_numeric(
        data.valorant_profile.current_rank_label
    )

    profile = RecruitGameProfile(
        application_id=app_obj.id,
        game_id=game.id,
        ign=data.valorant_profile.ign,
        current_rank_label=data.valorant_profile.current_rank_label,
        current_rank_numeric=rank_numeric,
        peak_rank_label=data.valorant_profile.peak_rank_label,
        primary_role=data.valorant_profile.primary_role,
        secondary_role=data.valorant_profile.secondary_role,
        tracker_url=data.valorant_profile.tracker_url,
        team_experience=data.valorant_profile.team_experience,
        scrim_experience=data.valorant_profile.scrim_experience,
        tournament_experience=data.valorant_profile.tournament_experience
    )

    db.add(profile)
    db.commit()

    # Run scoring
    inputs = ValorantInputs(
        rank_numeric=rank_numeric,
        hours_per_week=data.availability.hours_per_week,
        weeknights_available=data.availability.weeknights_available,
        weekends_available=data.availability.weekends_available,
        team_experience=data.valorant_profile.team_experience,
        scrim_experience=data.valorant_profile.scrim_experience,
        tournament_experience=data.valorant_profile.tournament_experience,
        tracker_url_present=bool(data.valorant_profile.tracker_url),
        ign_present=True,
        roles_present=True,
        peak_rank_present=bool(data.valorant_profile.peak_rank_label)
    )

    score, explanation = score_valorant(inputs)

    ranking = RecruitRanking(
        application_id=app_obj.id,
        game_id=game.id,
        score=score,
        explanation_json=explanation,
        model_version="v1_valorant"
    )

    db.add(ranking)
    db.commit()

    return {
        "message": "Application submitted",
        "score": score,
        "explanation": explanation
    }
