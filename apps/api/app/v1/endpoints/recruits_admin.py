from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import SessionLocal
from app.core.deps import require_admin
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
    RecruitReview,
    RECRUIT_REVIEW_STATUSES,
)
from app.schemas.admin import (
    RecruitStatusUpdate,
    RecruitNotesUpdate,
    RecruitTrainingExportResponse,
)
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_score_components_summary(explanation_json: Any) -> list[dict[str, float | str | None]] | None:
    if not isinstance(explanation_json, dict):
        return None

    components = explanation_json.get("components")
    if not isinstance(components, dict):
        return None

    def to_float(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return None

    rows: list[dict[str, float | str | None]] = []
    for component_name, component_values in components.items():
        if not isinstance(component_values, dict):
            continue
        rows.append(
            {
                "component": str(component_name),
                "raw": to_float(component_values.get("raw")),
                "weight": to_float(component_values.get("weight")),
                "contribution": to_float(component_values.get("contribution")),
            }
        )

    def contribution_key(item: dict[str, float | str | None]) -> float:
        value = item.get("contribution")
        return float(value) if isinstance(value, (int, float)) else float("-inf")

    rows.sort(key=contribution_key, reverse=True)
    return rows[:5]


@router.get("/admin/recruits/game/{game_slug}")
def list_recruits_for_game(
    game_slug: str,
    status: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    normalized_status = status.upper() if status else None
    if normalized_status and normalized_status not in RECRUIT_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

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
            AdminUser.username,
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
            & (RecruitRanking.game_id == game.id)
            & (RecruitRanking.is_current.is_(True)),
        )
        .outerjoin(
            RecruitReview,
            RecruitReview.application_id == RecruitApplication.id,
        )
        .outerjoin(
            AdminUser,
            AdminUser.id == RecruitReview.reviewer_user_id,
        )
        .filter(RecruitGameProfile.game_id == game.id)
    )

    if normalized_status:
        if normalized_status == "NEW":
            query = query.filter(
                or_(RecruitReview.status == normalized_status, RecruitReview.status.is_(None))
            )
        else:
            query = query.filter(RecruitReview.status == normalized_status)

    if min_score is not None:
        query = query.filter(RecruitRanking.score >= min_score)

    rows = query.all()

    results = []
    for app, avail, profile, ranking, review, reviewer_username in rows:
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
                "tournament_experience_details": profile.tournament_experience_details,
                "score": ranking.score if ranking else None,
                "score_model_version": ranking.model_version if ranking else None,
                "score_scoring_method": ranking.scoring_method if ranking else None,
                "score_scored_at": ranking.scored_at if ranking else None,
                "score_is_current": ranking.is_current if ranking else None,
                "score_components": (
                    ranking.explanation_json.get("components")
                    if ranking and isinstance(ranking.explanation_json, dict)
                    else None
                ),
                "status": review.status if review else "NEW",
                "review_labeled_at": review.labeled_at if review else None,
                "reviewer_username": reviewer_username,
            }
        )

    results.sort(key=lambda x: (x["score"] is not None, x["score"]), reverse=True)
    return results


@router.get("/admin/recruits/export/training", response_model=RecruitTrainingExportResponse)
def export_recruit_training_data(
    game_slug: str | None = Query(default=None),
    status: str | None = Query(default=None),
    submitted_from: datetime | None = Query(default=None),
    submitted_to: datetime | None = Query(default=None),
    limit: int = Query(default=2000, ge=1, le=10000),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    normalized_status = status.upper() if status else None
    if normalized_status and normalized_status not in RECRUIT_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    query = (
        db.query(
            RecruitApplication,
            RecruitGameProfile,
            Game,
            RecruitRanking,
            RecruitReview,
            AdminUser.username,
        )
        .join(
            RecruitGameProfile,
            RecruitGameProfile.application_id == RecruitApplication.id,
        )
        .join(
            Game,
            Game.id == RecruitGameProfile.game_id,
        )
        .outerjoin(
            RecruitRanking,
            (RecruitRanking.application_id == RecruitApplication.id)
            & (RecruitRanking.game_id == RecruitGameProfile.game_id)
            & (RecruitRanking.is_current.is_(True)),
        )
        .outerjoin(
            RecruitReview,
            RecruitReview.application_id == RecruitApplication.id,
        )
        .outerjoin(
            AdminUser,
            AdminUser.id == RecruitReview.reviewer_user_id,
        )
    )

    if game_slug:
        query = query.filter(Game.slug == game_slug)

    if normalized_status:
        if normalized_status == "NEW":
            query = query.filter(
                or_(RecruitReview.status == normalized_status, RecruitReview.status.is_(None))
            )
        else:
            query = query.filter(RecruitReview.status == normalized_status)

    if submitted_from is not None:
        query = query.filter(RecruitApplication.created_at >= submitted_from)

    if submitted_to is not None:
        query = query.filter(RecruitApplication.created_at <= submitted_to)

    rows = (
        query.order_by(RecruitApplication.created_at.desc(), RecruitApplication.id.desc())
        .limit(limit)
        .all()
    )

    export_rows = []
    for app, _profile, game, ranking, review, reviewer_username in rows:
        explanation_json = ranking.explanation_json if ranking else None
        review_status = (
            review.status
            if review and review.status in RECRUIT_REVIEW_STATUSES
            else "NEW"
        )
        export_rows.append(
            {
                "application_id": app.id,
                "game_id": game.id,
                "game_slug": game.slug,
                "submitted_at": app.created_at,
                "score": ranking.score if ranking else None,
                "scoring_method": ranking.scoring_method if ranking else None,
                "model_version": ranking.model_version if ranking else None,
                "scored_at": ranking.scored_at if ranking else None,
                "raw_inputs_json": ranking.raw_inputs_json if ranking else None,
                "normalized_features_json": (
                    ranking.normalized_features_json if ranking else None
                ),
                "explanation_json": explanation_json,
                "score_components_summary": _build_score_components_summary(explanation_json),
                "review_status": review_status,
                "label_reason": review.label_reason if review else None,
                "labeled_at": review.labeled_at if review else None,
                "reviewer_user_id": review.reviewer_user_id if review else None,
                "reviewer_username": reviewer_username,
            }
        )

    return {"count": len(export_rows), "rows": export_rows}

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
        .order_by(
            RecruitRanking.is_current.desc(),
            RecruitRanking.scored_at.desc(),
            RecruitRanking.id.desc(),
        )
        .all()
    )

    review = (
        db.query(RecruitReview)
        .filter(RecruitReview.application_id == application_id)
        .first()
    )
    reviewer_username = None
    if review and review.reviewer_user_id is not None:
        reviewer_username = (
            db.query(AdminUser.username)
            .filter(AdminUser.id == review.reviewer_user_id)
            .scalar()
        )

    current_ranking = next((r for r in rankings if r.is_current), None)

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
                "epic_games_name": p.epic_games_name,
                "fortnite_pr": p.fortnite_pr,
                "fortnite_kd": p.fortnite_kd,
                "fortnite_total_kills": p.fortnite_total_kills,
                "fortnite_playtime_hours": p.fortnite_playtime_hours,
                "fortnite_wins": p.fortnite_wins,
                "faceit_level": p.faceit_level,
                "faceit_elo": p.faceit_elo,
                "cs2_roles": p.cs2_roles,
                "prior_team_history": p.prior_team_history,
                "team_experience": p.team_experience,
                "scrim_experience": p.scrim_experience,
                "tournament_experience": p.tournament_experience,
                "tournament_experience_details": p.tournament_experience_details,
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
                "raw_inputs_json": r.raw_inputs_json,
                "normalized_features_json": r.normalized_features_json,
                "scoring_method": r.scoring_method,
                "is_current": r.is_current,
                "scored_at": r.scored_at,
            }
            for r in rankings
        ],
        "current_ranking": (
            {
                "game_id": current_ranking.game_id,
                "score": current_ranking.score,
                "explanation_json": current_ranking.explanation_json,
                "model_version": current_ranking.model_version,
                "raw_inputs_json": current_ranking.raw_inputs_json,
                "normalized_features_json": current_ranking.normalized_features_json,
                "scoring_method": current_ranking.scoring_method,
                "is_current": current_ranking.is_current,
                "scored_at": current_ranking.scored_at,
            }
            if current_ranking
            else None
        ),
        "review": {
            "status": review.status if review else "NEW",
            "notes": review.notes if review else None,
            "label_reason": review.label_reason if review else None,
            "labeled_at": review.labeled_at if review else None,
            "reviewer_user_id": review.reviewer_user_id if review else None,
            "reviewer_username": reviewer_username,
        },
    }
    
@router.patch("/admin/recruit/{application_id}/status")
def update_recruit_status(
    application_id: int,
    data: RecruitStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    app_exists = (
        db.query(RecruitApplication.id)
        .filter(RecruitApplication.id == application_id)
        .first()
    )
    if not app_exists:
        raise HTTPException(status_code=404, detail="Recruit not found")

    reviewer_user_id = None
    reviewer_username = user.get("sub")
    if reviewer_username:
        reviewer = (
            db.query(AdminUser)
            .filter(AdminUser.username == reviewer_username)
            .first()
        )
        reviewer_user_id = reviewer.id if reviewer else None

    now = datetime.utcnow()
    label_reason = data.label_reason.strip() if data.label_reason and data.label_reason.strip() else None

    review = (
        db.query(RecruitReview)
        .filter(RecruitReview.application_id == application_id)
        .first()
    )

    if not review:
        review = RecruitReview(
            application_id=application_id,
            status=data.status,
            reviewer_user_id=reviewer_user_id,
            labeled_at=now,
            label_reason=label_reason,
            notes=None,
            updated_at=now,
        )
        db.add(review)
    else:
        review.status = data.status
        review.reviewer_user_id = reviewer_user_id
        review.labeled_at = now
        review.label_reason = label_reason
        review.updated_at = now

    db.commit()
    return {
        "message": "Status updated",
        "status": review.status,
        "label_reason": review.label_reason,
        "labeled_at": review.labeled_at,
        "reviewer_user_id": review.reviewer_user_id,
        "reviewer_username": reviewer_username,
    }

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
            labeled_at=None,
            label_reason=None,
            notes=data.notes,
            updated_at=datetime.utcnow(),
        )
        db.add(review)
    else:
        review.notes = data.notes
        review.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "Notes updated", "notes": review.notes}
