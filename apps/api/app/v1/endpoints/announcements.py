import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased, selectinload

from app.core.config import get_settings
from app.core.deps import (
    StaffPrincipal,
    ensure_game_access,
    get_db,
    require_announcement_deleter,
    require_announcement_manager,
)
from app.core.uploads import ImageUploadConfig, delete_uploaded_image, save_uploaded_image
from app.models.admin_user import AdminUser
from app.models.announcement import EsportsAnnouncement
from app.models.game import Game
from app.schemas.announcement import (
    AnnouncementAdminOut,
    AnnouncementPublicOut,
    AnnouncementState,
    AnnouncementUpdateRequest,
)

router = APIRouter()

settings = get_settings()
NEWS_IMAGE_UPLOAD = ImageUploadConfig(
    upload_dir=settings.uploads_root_path / "news",
    public_prefix="/uploads/news",
    blob_prefix="news",
    max_upload_bytes=int(os.getenv("NEWS_IMAGE_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
    non_image_error_detail="Uploaded file must be an image",
    file_size_subject="Image",
)
ANNOUNCEMENT_STATES: set[str] = {"draft", "pending_approval", "published", "rejected"}
PUBLISHER_ROLES = {"coach", "head_coach", "admin"}


def _save_uploaded_image(upload: UploadFile) -> str:
    return save_uploaded_image(upload, NEWS_IMAGE_UPLOAD)


def _delete_uploaded_image(image_path: str | None) -> bool:
    return delete_uploaded_image(image_path, NEWS_IMAGE_UPLOAD)


def _normalize_state(raw_state: str | None) -> AnnouncementState:
    candidate = (raw_state or "published").strip().lower()
    if candidate in ANNOUNCEMENT_STATES:
        return candidate  # type: ignore[return-value]
    return "published"


def _can_publish(staff: StaffPrincipal) -> bool:
    return staff.role in PUBLISHER_ROLES


def _normalize_requested_game_slugs(
    game_slug: str | None,
    game_slugs: list[str] | None,
) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    raw_values: list[str] = []
    if game_slug is not None:
        raw_values.append(game_slug)
    if game_slugs:
        raw_values.extend(game_slugs)

    for raw_value in raw_values:
        slug = raw_value.strip().lower()
        if not slug or slug in seen:
            continue
        seen.add(slug)
        normalized.append(slug)

    return normalized


def _resolve_games_for_staff(
    db: Session,
    staff: StaffPrincipal,
    game_slugs: list[str],
) -> list[Game]:
    if not game_slugs:
        return []

    games = db.query(Game).filter(Game.slug.in_(tuple(game_slugs))).all()
    games_by_slug = {game.slug: game for game in games if game.slug}

    missing_slugs = [slug for slug in game_slugs if slug not in games_by_slug]
    if missing_slugs:
        raise HTTPException(status_code=404, detail=f"Games not found: {', '.join(missing_slugs)}")

    ordered_games = [games_by_slug[slug] for slug in game_slugs]
    for game in ordered_games:
        ensure_game_access(staff, game.id)
    return ordered_games


def _resolve_public_game_by_slug(db: Session, game_slug: str) -> Game:
    normalized_slug = game_slug.strip().lower()
    if not normalized_slug:
        raise HTTPException(status_code=400, detail="game_slug is required")

    game = db.query(Game).filter(Game.slug == normalized_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


def _announcement_game_entries(item: EsportsAnnouncement) -> list[tuple[str, str, int]]:
    entries: list[tuple[str, str, int]] = []
    seen_game_ids: set[int] = set()

    def add_game(game: Game | None) -> None:
        if not game or game.id is None or not game.slug:
            return

        game_id = int(game.id)
        if game_id in seen_game_ids:
            return

        seen_game_ids.add(game_id)
        entries.append((game.slug, game.name or game.slug, game_id))

    add_game(item.primary_game)
    for game in item.games:
        add_game(game)

    return entries


def _announcement_game_ids(item: EsportsAnnouncement) -> set[int]:
    game_ids = {game_id for _slug, _name, game_id in _announcement_game_entries(item)}
    if item.game_id is not None:
        game_ids.add(int(item.game_id))
    for game in item.games:
        if game.id is not None:
            game_ids.add(int(game.id))
    return game_ids


def _can_staff_access_announcement(staff: StaffPrincipal, announcement: EsportsAnnouncement) -> bool:
    if staff.has_global_game_access:
        return True

    # General announcements are intentionally global-only to preserve existing scoped permissions.
    if bool(announcement.is_general):
        return False

    game_ids = _announcement_game_ids(announcement)
    if not game_ids:
        return False

    return game_ids.issubset(staff.allowed_game_ids)


def _ensure_general_scope(staff: StaffPrincipal, is_general: bool) -> None:
    if not is_general:
        return

    # General announcements are intentionally global-only to preserve existing scoped permissions.
    if not staff.has_global_game_access:
        raise HTTPException(
            status_code=403,
            detail="Only staff with global game access can use the General tag",
        )


def _ensure_announcement_scope(staff: StaffPrincipal, announcement: EsportsAnnouncement) -> None:
    if _can_staff_access_announcement(staff, announcement):
        return
    raise HTTPException(status_code=403, detail="Forbidden for this announcement")


def _ensure_can_edit(staff: StaffPrincipal, announcement: EsportsAnnouncement) -> None:
    if staff.role in {"head_coach", "admin", "coach"}:
        return

    if staff.role == "captain":
        if announcement.created_by_admin_id != staff.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        if _normalize_state(announcement.state) == "published":
            raise HTTPException(status_code=403, detail="Published announcements cannot be edited")
        return

    raise HTTPException(status_code=403, detail="Forbidden")


def _coerce_workflow_action(raw_action: str | None, default_action: str) -> str:
    action = (raw_action or default_action).strip().lower()
    if action not in {"save_draft", "submit_for_approval", "publish", "reject"}:
        raise HTTPException(status_code=400, detail="Invalid workflow action")
    return action


def _set_workflow_state(
    announcement: EsportsAnnouncement,
    staff: StaffPrincipal,
    action: str,
) -> None:
    if action == "save_draft":
        announcement.state = "draft"
        announcement.approved_by_admin_id = None
        announcement.approved_at = None
        return

    if action == "submit_for_approval":
        announcement.state = "pending_approval"
        announcement.approved_by_admin_id = None
        announcement.approved_at = None
        return

    if action == "publish":
        if not _can_publish(staff):
            raise HTTPException(status_code=403, detail="Only coach or above can publish announcements")
        announcement.state = "published"
        announcement.approved_by_admin_id = staff.user_id
        announcement.approved_at = datetime.utcnow()
        return

    if action == "reject":
        if not _can_publish(staff):
            raise HTTPException(status_code=403, detail="Only coach or above can reject announcements")
        announcement.state = "rejected"
        announcement.approved_by_admin_id = None
        announcement.approved_at = None
        return

    raise HTTPException(status_code=400, detail="Unsupported workflow action")


def _build_admin_query(db: Session):
    creator = aliased(AdminUser)
    approver = aliased(AdminUser)
    return (
        db.query(
            EsportsAnnouncement,
            creator.username,
            approver.username,
        )
        .outerjoin(creator, creator.id == EsportsAnnouncement.created_by_admin_id)
        .outerjoin(approver, approver.id == EsportsAnnouncement.approved_by_admin_id)
        .options(selectinload(EsportsAnnouncement.games))
    )


def _serialize_public(item: EsportsAnnouncement) -> AnnouncementPublicOut:
    game_entries = _announcement_game_entries(item)
    primary_slug = game_entries[0][0] if game_entries else None
    primary_name = game_entries[0][1] if game_entries else None

    return AnnouncementPublicOut(
        id=item.id,
        title=item.title,
        body=item.body,
        image_url=item.image_path,
        state=_normalize_state(item.state),
        game_slug=primary_slug,
        game_name=primary_name,
        game_slugs=[slug for slug, _name, _game_id in game_entries],
        game_names=[name for _slug, name, _game_id in game_entries],
        is_general=bool(item.is_general),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_admin(
    item: EsportsAnnouncement,
    created_by_username: str | None,
    approved_by_username: str | None,
) -> AnnouncementAdminOut:
    public_payload = _serialize_public(item)
    return AnnouncementAdminOut(
        **public_payload.model_dump(),
        created_by_admin_id=item.created_by_admin_id,
        created_by_username=created_by_username,
        approved_by_admin_id=item.approved_by_admin_id,
        approved_by_username=approved_by_username,
        approved_at=item.approved_at,
    )


def _fetch_admin_announcement(
    db: Session,
    announcement_id: int,
) -> tuple[EsportsAnnouncement, str | None, str | None] | None:
    return (
        _build_admin_query(db)
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )


def _apply_public_game_filter(query, game: Game | None):
    if not game:
        return query

    return query.filter(
        or_(
            EsportsAnnouncement.is_general.is_(True),
            EsportsAnnouncement.game_id == game.id,
            EsportsAnnouncement.games.any(Game.id == game.id),
        )
    )


@router.post("/admin/news", response_model=AnnouncementAdminOut)
def create_announcement(
    title: str = Form(..., min_length=1, max_length=255),
    body: str = Form(..., min_length=1),
    game_slug: str | None = Form(default=None),
    game_slugs: list[str] | None = Form(default=None),
    is_general: bool = Form(default=False),
    workflow_action: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    clean_title = title.strip()
    clean_body = body.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not clean_body:
        raise HTTPException(status_code=400, detail="Body is required")

    _ensure_general_scope(staff, is_general)

    requested_game_slugs = _normalize_requested_game_slugs(game_slug, game_slugs)
    selected_games = _resolve_games_for_staff(db, staff, requested_game_slugs)
    if not selected_games and not is_general:
        raise HTTPException(
            status_code=400,
            detail="At least one game must be selected when General is not enabled",
        )

    image_path = _save_uploaded_image(image) if image and image.filename else None

    default_action = "save_draft" if staff.role == "captain" else "publish"
    action = _coerce_workflow_action(workflow_action, default_action)
    if staff.role == "captain" and action in {"publish", "reject"}:
        raise HTTPException(status_code=403, detail="Captains cannot publish or reject announcements")

    announcement = EsportsAnnouncement(
        title=clean_title,
        body=clean_body,
        image_path=image_path,
        game_id=selected_games[0].id if selected_games else None,
        is_general=is_general,
        created_by_admin_id=staff.user_id,
    )
    announcement.games = selected_games
    _set_workflow_state(announcement, staff, action)

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    row = _fetch_admin_announcement(db, announcement.id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = row
    return _serialize_admin(item, creator_username, approver_username)


@router.get("/admin/news", response_model=list[AnnouncementAdminOut])
def list_announcements_admin(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    query = _build_admin_query(db)
    if not staff.has_global_game_access:
        if not staff.allowed_game_ids:
            return []

        allowed_game_ids = tuple(staff.allowed_game_ids)
        query = query.filter(
            or_(
                EsportsAnnouncement.game_id.in_(allowed_game_ids),
                EsportsAnnouncement.games.any(Game.id.in_(allowed_game_ids)),
            )
        )

    fetch_limit = limit if staff.has_global_game_access else min(max(limit * 5, limit), 2000)
    rows = (
        query.order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .limit(fetch_limit)
        .all()
    )

    items: list[AnnouncementAdminOut] = []
    for item, creator_username, approver_username in rows:
        if not _can_staff_access_announcement(staff, item):
            continue
        items.append(_serialize_admin(item, creator_username, approver_username))
        if len(items) >= limit:
            break

    return items


@router.get("/admin/news/{announcement_id}", response_model=AnnouncementAdminOut)
def get_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = row
    _ensure_announcement_scope(staff, item)
    return _serialize_admin(item, creator_username, approver_username)


@router.patch("/admin/news/{announcement_id}", response_model=AnnouncementAdminOut)
def update_announcement_admin(
    announcement_id: int,
    data: AnnouncementUpdateRequest,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username = row

    _ensure_announcement_scope(staff, announcement)
    _ensure_can_edit(staff, announcement)

    has_update = False

    if data.title is not None:
        clean_title = data.title.strip()
        if not clean_title:
            raise HTTPException(status_code=400, detail="Title is required")
        announcement.title = clean_title
        has_update = True

    if data.body is not None:
        clean_body = data.body.strip()
        if not clean_body:
            raise HTTPException(status_code=400, detail="Body is required")
        announcement.body = clean_body
        has_update = True

    if data.game_slugs is not None:
        selected_games = _resolve_games_for_staff(db, staff, data.game_slugs)
        announcement.games = selected_games
        announcement.game_id = selected_games[0].id if selected_games else None
        has_update = True

    if data.is_general is not None:
        _ensure_general_scope(staff, data.is_general)
        announcement.is_general = data.is_general
        has_update = True

    if not announcement.is_general and not _announcement_game_ids(announcement):
        raise HTTPException(
            status_code=400,
            detail="At least one game must be selected when General is not enabled",
        )

    if data.workflow_action is not None:
        action = _coerce_workflow_action(data.workflow_action, data.workflow_action)
        if staff.role == "captain" and action in {"publish", "reject"}:
            raise HTTPException(status_code=403, detail="Captains cannot publish or reject announcements")
        _set_workflow_state(announcement, staff, action)
        has_update = True

    if not has_update:
        raise HTTPException(status_code=400, detail="No update fields provided")

    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = updated
    return _serialize_admin(item, creator_username, approver_username)


@router.post("/admin/news/{announcement_id}/submit", response_model=AnnouncementAdminOut)
def submit_announcement_for_approval(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username = row

    _ensure_announcement_scope(staff, announcement)
    _ensure_can_edit(staff, announcement)
    _set_workflow_state(announcement, staff, "submit_for_approval")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = updated
    return _serialize_admin(item, creator_username, approver_username)


@router.post("/admin/news/{announcement_id}/publish", response_model=AnnouncementAdminOut)
def publish_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username = row

    _ensure_announcement_scope(staff, announcement)
    _set_workflow_state(announcement, staff, "publish")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = updated
    return _serialize_admin(item, creator_username, approver_username)


@router.post("/admin/news/{announcement_id}/reject", response_model=AnnouncementAdminOut)
def reject_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username = row

    _ensure_announcement_scope(staff, announcement)
    _set_workflow_state(announcement, staff, "reject")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username = updated
    return _serialize_admin(item, creator_username, approver_username)


@router.get("/news/latest", response_model=AnnouncementPublicOut | None)
def get_latest_announcement(
    game_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    game = _resolve_public_game_by_slug(db, game_slug) if game_slug else None

    query = (
        db.query(EsportsAnnouncement)
        .options(selectinload(EsportsAnnouncement.games))
        .filter(EsportsAnnouncement.state == "published")
    )
    query = _apply_public_game_filter(query, game)

    item = (
        query.order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .first()
    )
    if not item:
        return None
    return _serialize_public(item)


@router.get("/news/archive", response_model=list[AnnouncementPublicOut])
def list_archive_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    game_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    game = _resolve_public_game_by_slug(db, game_slug) if game_slug else None

    query = (
        db.query(EsportsAnnouncement)
        .options(selectinload(EsportsAnnouncement.games))
        .filter(EsportsAnnouncement.state == "published")
    )
    query = _apply_public_game_filter(query, game)

    rows = (
        query.order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .offset(1)
        .limit(limit)
        .all()
    )
    return [_serialize_public(item) for item in rows]


@router.get("/news", response_model=list[AnnouncementPublicOut])
def list_public_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    game_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    game = _resolve_public_game_by_slug(db, game_slug) if game_slug else None

    query = (
        db.query(EsportsAnnouncement)
        .options(selectinload(EsportsAnnouncement.games))
        .filter(EsportsAnnouncement.state == "published")
    )
    query = _apply_public_game_filter(query, game)

    rows = (
        query.order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_public(item) for item in rows]


@router.get("/news/{announcement_id}", response_model=AnnouncementPublicOut)
def get_announcement_public(
    announcement_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(EsportsAnnouncement)
        .options(selectinload(EsportsAnnouncement.games))
        .filter(
            EsportsAnnouncement.id == announcement_id,
            EsportsAnnouncement.state == "published",
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return _serialize_public(item)


@router.delete("/admin/news/{announcement_id}")
def delete_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_deleter),
):
    item = (
        db.query(EsportsAnnouncement)
        .options(selectinload(EsportsAnnouncement.games))
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    _ensure_announcement_scope(staff, item)

    image_path = item.image_path
    db.delete(item)
    db.commit()

    image_deleted = _delete_uploaded_image(image_path)
    return {
        "message": "Announcement deleted",
        "id": announcement_id,
        "image_deleted": image_deleted,
    }
