from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import (
    StaffPrincipal,
    get_db,
    require_roster_deleter,
    require_roster_manager,
    require_roster_viewer,
)
from app.models.staff_profile import StaffProfile
from app.schemas.staff import (
    StaffCategory,
    StaffProfileCreate,
    StaffProfileDetailOut,
    StaffProfileSummaryOut,
    StaffProfileUpdate,
)

router = APIRouter()

CATEGORY_ORDER: list[StaffCategory] = ["coach", "captain", "faculty", "advisor", "staff", "other"]
CATEGORY_SET = set(CATEGORY_ORDER)


def _normalize_filter_value(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip().lower()
    return normalized if normalized else None


def _normalize_slug(raw_slug: str) -> str:
    normalized = raw_slug.strip().lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="slug is required")
    return normalized


def _category_sort_expression():
    order_cases = [(StaffProfile.category == category, index) for index, category in enumerate(CATEGORY_ORDER)]
    return case(*order_cases, else_=len(CATEGORY_ORDER))


def _matches_game_scope(scope: object, game_filter: str) -> bool:
    if not game_filter:
        return True

    normalized_filter = game_filter.casefold()
    if isinstance(scope, str):
        return scope.strip().casefold() == normalized_filter

    if isinstance(scope, list):
        for item in scope:
            if isinstance(item, str) and item.strip().casefold() == normalized_filter:
                return True
    return False


def _apply_updates(profile: StaffProfile, payload: StaffProfileUpdate) -> bool:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return False

    for key, value in data.items():
        setattr(profile, key, value)
    return True


@router.get("/staff", response_model=list[StaffProfileSummaryOut])
def list_staff_profiles(
    category: str | None = Query(default=None),
    game: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    normalized_category = _normalize_filter_value(category)
    normalized_game = _normalize_filter_value(game)

    if normalized_category and normalized_category not in CATEGORY_SET:
        raise HTTPException(status_code=400, detail="Invalid staff category filter")

    query = db.query(StaffProfile).filter(StaffProfile.is_active.is_(True))
    if normalized_category:
        query = query.filter(StaffProfile.category == normalized_category)

    rows = (
        query.order_by(
            _category_sort_expression(),
            StaffProfile.sort_order.asc(),
            func.lower(StaffProfile.full_name).asc(),
            StaffProfile.id.asc(),
        ).all()
    )

    if normalized_game:
        rows = [row for row in rows if _matches_game_scope(row.game_scope, normalized_game)]

    return rows


@router.get("/staff/{slug}", response_model=StaffProfileDetailOut)
def get_staff_profile(
    slug: str,
    db: Session = Depends(get_db),
):
    normalized_slug = _normalize_slug(slug)
    item = (
        db.query(StaffProfile)
        .filter(StaffProfile.slug == normalized_slug, StaffProfile.is_active.is_(True))
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Staff profile not found")
    return item


@router.get("/admin/staff", response_model=list[StaffProfileDetailOut])
def list_staff_profiles_admin(
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_viewer),
):
    return (
        db.query(StaffProfile)
        .order_by(
            _category_sort_expression(),
            StaffProfile.sort_order.asc(),
            func.lower(StaffProfile.full_name).asc(),
            StaffProfile.id.asc(),
        )
        .all()
    )


@router.post("/admin/staff", response_model=StaffProfileDetailOut, status_code=status.HTTP_201_CREATED)
def create_staff_profile_admin(
    payload: StaffProfileCreate,
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_manager),
):
    profile = StaffProfile(**payload.model_dump())
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Staff profile slug already exists") from exc
    db.refresh(profile)
    return profile


@router.patch("/admin/staff/{staff_id}", response_model=StaffProfileDetailOut)
def update_staff_profile_admin(
    staff_id: int,
    payload: StaffProfileUpdate,
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_manager),
):
    profile = db.query(StaffProfile).filter(StaffProfile.id == staff_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Staff profile not found")

    has_updates = _apply_updates(profile, payload)
    if not has_updates:
        raise HTTPException(status_code=400, detail="No update fields provided")

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Staff profile slug already exists") from exc
    db.refresh(profile)
    return profile


@router.delete("/admin/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_staff_profile_admin(
    staff_id: int,
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_deleter),
):
    profile = db.query(StaffProfile).filter(StaffProfile.id == staff_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Staff profile not found")

    profile.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
