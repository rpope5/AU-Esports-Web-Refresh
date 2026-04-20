from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.core.deps import (
    StaffPrincipal,
    apply_game_scope_filter,
    ensure_game_access,
    get_db,
    require_schedule_deleter,
    require_schedule_manager,
)
from app.models.admin_user import AdminUser
from app.models.calendar_event import CalendarEvent
from app.models.game import Game
from app.schemas.schedule import (
    CalendarEventAdminOut,
    CalendarEventCreate,
    CalendarEventPublicOut,
    CalendarEventUpdate,
    ScheduleStatus,
    ScheduleWorkflowAction,
)

router = APIRouter()

SCHEDULE_STATES: set[str] = {"pending", "published", "rejected", "archived"}
SCHEDULE_WORKFLOW_ACTIONS: set[str] = {
    "submit_for_approval",
    "publish",
    "reject",
    "archive",
}
PUBLISHER_ROLES: set[str] = {"coach", "head_coach", "admin"}


def _normalize_status(raw_state: str | None) -> ScheduleStatus:
    candidate = (raw_state or "published").strip().lower()
    if candidate in SCHEDULE_STATES:
        return candidate  # type: ignore[return-value]
    return "published"


def _can_publish(staff: StaffPrincipal) -> bool:
    return staff.role in PUBLISHER_ROLES


def _coerce_workflow_action(raw_action: str | None, default_action: str) -> ScheduleWorkflowAction:
    action = (raw_action or default_action).strip().lower()
    if action not in SCHEDULE_WORKFLOW_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid workflow action")
    return action  # type: ignore[return-value]


def _parse_status_filter(raw_status_filter: str | None) -> set[ScheduleStatus] | None:
    if raw_status_filter is None:
        return None

    requested_states = {
        status.strip().lower()
        for status in raw_status_filter.split(",")
        if status.strip()
    }
    if not requested_states:
        return None

    invalid_states = sorted(state for state in requested_states if state not in SCHEDULE_STATES)
    if invalid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status filter values: {', '.join(invalid_states)}",
        )
    return requested_states  # type: ignore[return-value]


def _resolve_game_for_staff(
    db: Session,
    staff: StaffPrincipal,
    game_slug: str | None,
    fallback_game: str | None,
    *,
    required: bool = True,
) -> Game | None:
    normalized_slug = (game_slug or "").strip().lower()
    if normalized_slug:
        game = db.query(Game).filter(Game.slug == normalized_slug).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        ensure_game_access(staff, game.id)
        return game

    normalized_game = (fallback_game or "").strip().lower()
    if normalized_game:
        game = (
            db.query(Game)
            .filter(
                or_(
                    Game.slug == normalized_game,
                    Game.name.ilike(normalized_game),
                )
            )
            .first()
        )
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        ensure_game_access(staff, game.id)
        return game

    if required:
        raise HTTPException(status_code=400, detail="game_slug is required")

    return None


def _ensure_event_scope(staff: StaffPrincipal, event: CalendarEvent) -> None:
    if staff.has_global_game_access:
        return
    if event.game_id is None:
        raise HTTPException(status_code=403, detail="Forbidden for this schedule item")
    ensure_game_access(staff, event.game_id)


def _ensure_can_edit(staff: StaffPrincipal, event: CalendarEvent) -> None:
    if staff.role in {"coach", "head_coach", "admin"}:
        return

    if staff.role == "captain":
        if event.created_by_admin_id != staff.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        if _normalize_status(event.status) != "pending":
            raise HTTPException(
                status_code=403,
                detail="Captains can only edit their own pending schedule items",
            )
        return

    raise HTTPException(status_code=403, detail="Forbidden")


def _set_workflow_state(
    event: CalendarEvent,
    staff: StaffPrincipal,
    action: ScheduleWorkflowAction,
) -> None:
    if action == "submit_for_approval":
        event.status = "pending"
        event.submitted_at = datetime.utcnow()
        event.approved_by_admin_id = None
        event.approved_at = None
        event.rejected_by_admin_id = None
        event.rejected_at = None
        event.archived_at = None
        return

    if action == "publish":
        if not _can_publish(staff):
            raise HTTPException(status_code=403, detail="Only coach or above can publish schedule items")
        event.status = "published"
        event.approved_by_admin_id = staff.user_id
        event.approved_at = datetime.utcnow()
        event.rejected_by_admin_id = None
        event.rejected_at = None
        event.archived_at = None
        return

    if action == "reject":
        if not _can_publish(staff):
            raise HTTPException(status_code=403, detail="Only coach or above can reject schedule items")
        event.status = "rejected"
        event.rejected_by_admin_id = staff.user_id
        event.rejected_at = datetime.utcnow()
        event.approved_by_admin_id = None
        event.approved_at = None
        event.archived_at = None
        return

    if action == "archive":
        if not _can_publish(staff):
            raise HTTPException(status_code=403, detail="Only coach or above can archive schedule items")
        event.status = "archived"
        event.archived_at = datetime.utcnow()
        return

    raise HTTPException(status_code=400, detail="Unsupported workflow action")


def _build_admin_query(db: Session):
    creator = aliased(AdminUser)
    approver = aliased(AdminUser)
    rejector = aliased(AdminUser)
    return (
        db.query(
            CalendarEvent,
            Game.slug,
            Game.name,
            creator.username,
            approver.username,
            rejector.username,
        )
        .outerjoin(Game, Game.id == CalendarEvent.game_id)
        .outerjoin(creator, creator.id == CalendarEvent.created_by_admin_id)
        .outerjoin(approver, approver.id == CalendarEvent.approved_by_admin_id)
        .outerjoin(rejector, rejector.id == CalendarEvent.rejected_by_admin_id)
    )


def _serialize_public(
    event: CalendarEvent,
    game_slug: str | None,
    game_name: str | None,
) -> CalendarEventPublicOut:
    return CalendarEventPublicOut(
        id=event.id,
        name=event.name,
        time=event.time,
        game=event.game or game_name,
        game_slug=game_slug,
        game_name=game_name or event.game,
        status=_normalize_status(event.status),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _serialize_admin(
    event: CalendarEvent,
    game_slug: str | None,
    game_name: str | None,
    created_by_username: str | None,
    approved_by_username: str | None,
    rejected_by_username: str | None,
) -> CalendarEventAdminOut:
    return CalendarEventAdminOut(
        id=event.id,
        name=event.name,
        time=event.time,
        game=event.game or game_name,
        game_slug=game_slug,
        game_name=game_name or event.game,
        status=_normalize_status(event.status),
        created_at=event.created_at,
        updated_at=event.updated_at,
        created_by_admin_id=event.created_by_admin_id,
        created_by_username=created_by_username,
        approved_by_admin_id=event.approved_by_admin_id,
        approved_by_username=approved_by_username,
        rejected_by_admin_id=event.rejected_by_admin_id,
        rejected_by_username=rejected_by_username,
        submitted_at=event.submitted_at,
        approved_at=event.approved_at,
        rejected_at=event.rejected_at,
        archived_at=event.archived_at,
    )


def _fetch_admin_event(
    db: Session,
    event_id: int,
) -> tuple[CalendarEvent, str | None, str | None, str | None, str | None, str | None] | None:
    return _build_admin_query(db).filter(CalendarEvent.id == event_id).first()


def _query_calendar_events_public(
    db: Session,
    start: datetime | None,
    end: datetime | None,
) -> list[CalendarEventPublicOut]:
    if start and end and end < start:
        raise HTTPException(status_code=400, detail="end must be greater than or equal to start")

    query = (
        db.query(CalendarEvent, Game.slug, Game.name)
        .outerjoin(Game, Game.id == CalendarEvent.game_id)
        .filter(CalendarEvent.status == "published")
    )
    if start is not None:
        query = query.filter(CalendarEvent.time >= start)
    if end is not None:
        query = query.filter(CalendarEvent.time <= end)

    rows = query.order_by(CalendarEvent.time.asc(), CalendarEvent.id.asc()).all()
    return [_serialize_public(item, game_slug, game_name) for item, game_slug, game_name in rows]


def _transition_event(
    event_id: int,
    action: ScheduleWorkflowAction,
    db: Session,
    staff: StaffPrincipal,
) -> CalendarEventAdminOut:
    row = _fetch_admin_event(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    event, _game_slug, _game_name, _creator, _approver, _rejector = row

    _ensure_event_scope(staff, event)
    _set_workflow_state(event, staff, action)
    db.commit()
    db.refresh(event)

    updated = _fetch_admin_event(db, event_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    item, game_slug, game_name, created_by_username, approved_by_username, rejected_by_username = updated
    return _serialize_admin(
        item,
        game_slug,
        game_name,
        created_by_username,
        approved_by_username,
        rejected_by_username,
    )


@router.get("/schedule/events", response_model=list[CalendarEventPublicOut])
def list_schedule_events(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return _query_calendar_events_public(db=db, start=start, end=end)


@router.get("/admin/schedule/events", response_model=list[CalendarEventAdminOut])
def list_schedule_events_admin(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    status: str | None = Query(default=None),
    game_slug: str | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    if start and end and end < start:
        raise HTTPException(status_code=400, detail="end must be greater than or equal to start")

    status_filter = _parse_status_filter(status)

    query = _build_admin_query(db)
    query = apply_game_scope_filter(query, CalendarEvent.game_id, staff)

    if start is not None:
        query = query.filter(CalendarEvent.time >= start)
    if end is not None:
        query = query.filter(CalendarEvent.time <= end)
    if status_filter:
        query = query.filter(CalendarEvent.status.in_(tuple(status_filter)))
    if game_slug:
        game = _resolve_game_for_staff(db, staff, game_slug=game_slug, fallback_game=None, required=True)
        if game:
            query = query.filter(CalendarEvent.game_id == game.id)

    rows = (
        query.order_by(CalendarEvent.time.asc(), CalendarEvent.id.asc())
        .limit(limit)
        .all()
    )
    return [
        _serialize_admin(
            item,
            row_game_slug,
            row_game_name,
            created_by_username,
            approved_by_username,
            rejected_by_username,
        )
        for item, row_game_slug, row_game_name, created_by_username, approved_by_username, rejected_by_username in rows
    ]


@router.post("/admin/schedule/events", response_model=CalendarEventAdminOut, status_code=201)
def create_schedule_event(
    data: CalendarEventCreate,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    game = _resolve_game_for_staff(
        db,
        staff,
        game_slug=data.game_slug,
        fallback_game=data.game,
        required=True,
    )
    if not game:
        raise HTTPException(status_code=400, detail="Game is required")

    default_action = "submit_for_approval" if staff.role == "captain" else "publish"
    action = _coerce_workflow_action(data.workflow_action, default_action)

    if staff.role == "captain" and action != "submit_for_approval":
        raise HTTPException(status_code=403, detail="Captains cannot directly publish schedule items")
    if staff.role != "captain" and action in {"reject", "archive"}:
        raise HTTPException(status_code=400, detail="Invalid create workflow action")

    event = CalendarEvent(
        name=data.name,
        time=data.time,
        game=game.name,
        game_id=game.id,
        created_by_admin_id=staff.user_id,
    )
    _set_workflow_state(event, staff, action)

    db.add(event)
    db.commit()
    db.refresh(event)

    row = _fetch_admin_event(db, event.id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    item, game_slug, game_name, created_by_username, approved_by_username, rejected_by_username = row
    return _serialize_admin(
        item,
        game_slug,
        game_name,
        created_by_username,
        approved_by_username,
        rejected_by_username,
    )


@router.patch("/admin/schedule/events/{event_id}", response_model=CalendarEventAdminOut)
def update_schedule_event(
    event_id: int,
    data: CalendarEventUpdate,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    row = _fetch_admin_event(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    event, _game_slug, _game_name, _created_by_username, _approved_by_username, _rejected_by_username = row

    _ensure_event_scope(staff, event)
    _ensure_can_edit(staff, event)

    update_data = data.model_dump(exclude_unset=True)
    has_update = False

    if "name" in update_data:
        if update_data["name"] is None:
            raise HTTPException(status_code=400, detail="name cannot be null")
        event.name = update_data["name"]
        has_update = True
    if "time" in update_data:
        if update_data["time"] is None:
            raise HTTPException(status_code=400, detail="time cannot be null")
        event.time = update_data["time"]
        has_update = True
    if "game_slug" in update_data or "game" in update_data:
        game = _resolve_game_for_staff(
            db,
            staff,
            game_slug=update_data.get("game_slug"),
            fallback_game=update_data.get("game"),
            required=True,
        )
        if not game:
            raise HTTPException(status_code=400, detail="Game is required")
        event.game_id = game.id
        event.game = game.name
        has_update = True
    if "workflow_action" in update_data:
        if update_data.get("workflow_action") is None:
            raise HTTPException(status_code=400, detail="workflow_action cannot be null")
        action = _coerce_workflow_action(
            update_data.get("workflow_action"),
            update_data.get("workflow_action"),
        )
        if staff.role == "captain" and action != "submit_for_approval":
            raise HTTPException(status_code=403, detail="Captains cannot directly publish or reject schedule items")
        _set_workflow_state(event, staff, action)
        has_update = True

    if not has_update:
        raise HTTPException(status_code=400, detail="No update fields provided")

    db.commit()
    db.refresh(event)

    updated = _fetch_admin_event(db, event_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    item, game_slug, game_name, created_by_username, approved_by_username, rejected_by_username = updated
    return _serialize_admin(
        item,
        game_slug,
        game_name,
        created_by_username,
        approved_by_username,
        rejected_by_username,
    )


@router.post("/admin/schedule/events/{event_id}/submit", response_model=CalendarEventAdminOut)
def submit_schedule_event_for_approval(
    event_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    row = _fetch_admin_event(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    event, _game_slug, _game_name, _creator, _approver, _rejector = row
    _ensure_event_scope(staff, event)
    _ensure_can_edit(staff, event)
    return _transition_event(event_id, "submit_for_approval", db, staff)


@router.post("/admin/schedule/events/{event_id}/approve", response_model=CalendarEventAdminOut)
@router.post("/admin/schedule/events/{event_id}/publish", response_model=CalendarEventAdminOut)
def approve_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    return _transition_event(event_id, "publish", db, staff)


@router.post("/admin/schedule/events/{event_id}/reject", response_model=CalendarEventAdminOut)
def reject_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    return _transition_event(event_id, "reject", db, staff)


@router.post("/admin/schedule/events/{event_id}/archive", response_model=CalendarEventAdminOut)
def archive_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_manager),
):
    return _transition_event(event_id, "archive", db, staff)


@router.delete("/admin/schedule/events/{event_id}", status_code=204)
def delete_schedule_event(
    event_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_schedule_deleter),
):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    _ensure_event_scope(staff, event)

    db.delete(event)
    db.commit()
    return Response(status_code=204)
