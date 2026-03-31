from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.deps import require_admin
from app.models.game import Game
from app.models.recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
    RecruitReview,
)
from app.schemas.admin import RecruitStatusUpdate, RecruitNotesUpdate
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/admin/recruits/game/{game_slug}")
def list_recruits_for_game(
    game_slug: str,
    status: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    game = db.query(Game).filter(Game.slug == game_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    query = (
        db.query(
            RecruitApplication,
            RecruitAvailability,
            RecruitGameProfile,
            RecruitRanking,
            RecruitReview,
        )
        .join(
            RecruitGameProfile,
            RecruitGameProfile.application_id == RecruitApplication.id,
        )
        .outerjoin(
            RecruitAvailability,
            RecruitAvailability.application_id == RecruitApplication.id,
        )
        .outerjoin(
            RecruitRanking,
            (RecruitRanking.application_id == RecruitApplication.id)
            & (RecruitRanking.game_id == game.id),
        )
        .outerjoin(
            RecruitReview,
            RecruitReview.application_id == RecruitApplication.id,
        )
        .filter(RecruitGameProfile.game_id == game.id)
    )

    if status:
        query = query.filter(RecruitReview.status == status.upper())

    if min_score is not None:
        query = query.filter(RecruitRanking.score >= min_score)

    rows = query.all()

    results = []
    for app, avail, profile, ranking, review in rows:
        results.append(
            {
                "application_id": app.id,
                "first_name": app.first_name,
                "last_name": app.last_name,
                "email": app.email,
                "discord": app.discord,
                "graduation_year": app.graduation_year,
                "current_school": app.current_school,
                "hours_per_week": avail.hours_per_week if avail else None,
                "weeknights_available": avail.weeknights_available if avail else None,
                "weekends_available": avail.weekends_available if avail else None,
                "ign": profile.ign,
                "current_rank_label": profile.current_rank_label,
                "primary_role": profile.primary_role,
                "secondary_role": profile.secondary_role,
                "tracker_url": profile.tracker_url,
                "team_experience": profile.team_experience,
                "scrim_experience": profile.scrim_experience,
                "tournament_experience": profile.tournament_experience,
                "score": ranking.score if ranking else None,
                "status": review.status if review else "NEW",
            }
        )

    results.sort(key=lambda x: (x["score"] is not None, x["score"]), reverse=True)
    return results

@router.get("/admin/recruit/{application_id}")
def get_recruit_detail(
    application_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    app = (
        db.query(RecruitApplication)
        .filter(RecruitApplication.id == application_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Recruit not found")

    availability = (
        db.query(RecruitAvailability)
        .filter(RecruitAvailability.application_id == application_id)
        .first()
    )

    profiles = (
        db.query(RecruitGameProfile, Game)
        .outerjoin(Game, RecruitGameProfile.game_id == Game.id)
        .filter(RecruitGameProfile.application_id == application_id)
        .all()
    )

    rankings = (
        db.query(RecruitRanking)
        .filter(RecruitRanking.application_id == application_id)
        .all()
    )

    review = (
        db.query(RecruitReview)
        .filter(RecruitReview.application_id == application_id)
        .first()
    )

    return {
        "application": {
            "id": app.id,
            "first_name": app.first_name,
            "last_name": app.last_name,
            "email": app.email,
            "discord": app.discord,
            "current_school": app.current_school,
            "city_state": app.city_state,
            "graduation_year": app.graduation_year,
            "preferred_contact": app.preferred_contact,
            "created_at": app.created_at,
        },
        "availability": {
            "hours_per_week": availability.hours_per_week if availability else None,
            "weeknights_available": availability.weeknights_available if availability else None,
            "weekends_available": availability.weekends_available if availability else None,
        },
        "profiles": [
            {
                "game_id": p.game_id,
                "game_name": game.name if game else None,
                "game_slug": game.slug if game else None,
                "ign": p.ign,
                "current_rank_label": p.current_rank_label,
                "current_rank_numeric": p.current_rank_numeric,
                "peak_rank_label": p.peak_rank_label,
                "peak_rank_numeric": p.peak_rank_numeric,
                "primary_role": p.primary_role,
                "secondary_role": p.secondary_role,
                "tracker_url": p.tracker_url,
                "team_experience": p.team_experience,
                "scrim_experience": p.scrim_experience,
                "tournament_experience": p.tournament_experience,
                "ranked_wins": p.ranked_wins,
                "years_played": p.years_played,
                "legend_peak_rank": p.legend_peak_rank,
                "preferred_format": p.preferred_format,
                "other_card_games": p.other_card_games,
                "gsp": p.gsp,
                "regional_rank": p.regional_rank,
                "best_wins": p.best_wins,
                "characters": p.characters,
                "lounge_rating": p.lounge_rating,
                "preferred_title": p.preferred_title,
                "controller_type": p.controller_type,
                "playstyle": p.playstyle,
                "preferred_tracks": p.preferred_tracks,
            }
            for p, game in profiles
        ],
        "rankings": [
            {
                "game_id": r.game_id,
                "score": r.score,
                "explanation_json": r.explanation_json,
                "model_version": r.model_version,
            }
            for r in rankings
        ],
        "review": {
            "status": review.status if review else "NEW",
            "notes": review.notes if review else None,
        },
    }
    
@router.patch("/admin/recruit/{application_id}/status")
def update_recruit_status(
    application_id: int,
    data: RecruitStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    review = (
        db.query(RecruitReview)
        .filter(RecruitReview.application_id == application_id)
        .first()
    )

    if not review:
        review = RecruitReview(
            application_id=application_id,
            status=data.status.upper(),
            reviewer_user_id=None,
            notes=None,
            updated_at=datetime.utcnow(),
        )
        db.add(review)
    else:
        review.status = data.status.upper()
        review.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Status updated", "status": review.status}

@router.patch("/admin/recruit/{application_id}/notes")
def update_recruit_notes(
    application_id: int,
    data: RecruitNotesUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    review = (
        db.query(RecruitReview)
        .filter(RecruitReview.application_id == application_id)
        .first()
    )

    if not review:
        review = RecruitReview(
            application_id=application_id,
            status="NEW",
            reviewer_user_id=None,
            notes=data.notes,
            updated_at=datetime.utcnow(),
        )
        db.add(review)
    else:
        review.notes = data.notes
        review.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Notes updated", "notes": review.notes}