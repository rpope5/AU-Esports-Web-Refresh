import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, aliased

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

API_ROOT = Path(__file__).resolve().parents[3]
NEWS_IMAGE_UPLOAD = ImageUploadConfig(
    upload_dir=API_ROOT / "uploads" / "news",
    public_prefix="/uploads/news",
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


def _ensure_announcement_scope(staff: StaffPrincipal, announcement: EsportsAnnouncement) -> None:
    if staff.has_global_game_access:
        return
    if announcement.game_id is None:
        raise HTTPException(status_code=403, detail="Forbidden for this announcement")
    ensure_game_access(staff, announcement.game_id)


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
            Game.slug,
            Game.name,
        )
        .outerjoin(creator, creator.id == EsportsAnnouncement.created_by_admin_id)
        .outerjoin(approver, approver.id == EsportsAnnouncement.approved_by_admin_id)
        .outerjoin(Game, Game.id == EsportsAnnouncement.game_id)
    )


def _serialize_public(
    item: EsportsAnnouncement,
    game_slug: str | None,
    game_name: str | None,
) -> AnnouncementPublicOut:
    return AnnouncementPublicOut(
        id=item.id,
        title=item.title,
        body=item.body,
        image_url=item.image_path,
        state=_normalize_state(item.state),
        game_slug=game_slug,
        game_name=game_name,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_admin(
    item: EsportsAnnouncement,
    created_by_username: str | None,
    approved_by_username: str | None,
    game_slug: str | None,
    game_name: str | None,
) -> AnnouncementAdminOut:
    return AnnouncementAdminOut(
        id=item.id,
        title=item.title,
        body=item.body,
        image_url=item.image_path,
        state=_normalize_state(item.state),
        game_slug=game_slug,
        game_name=game_name,
        created_at=item.created_at,
        updated_at=item.updated_at,
        created_by_admin_id=item.created_by_admin_id,
        created_by_username=created_by_username,
        approved_by_admin_id=item.approved_by_admin_id,
        approved_by_username=approved_by_username,
        approved_at=item.approved_at,
    )


def _fetch_admin_announcement(
    db: Session,
    announcement_id: int,
) -> tuple[EsportsAnnouncement, str | None, str | None, str | None, str | None] | None:
    return (
        _build_admin_query(db)
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )


def _resolve_game_for_staff(db: Session, staff: StaffPrincipal, game_slug: str) -> Game:
    normalized_slug = game_slug.strip().lower()
    if not normalized_slug:
        raise HTTPException(status_code=400, detail="game_slug is required")

    game = db.query(Game).filter(Game.slug == normalized_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    ensure_game_access(staff, game.id)
    return game


@router.post("/admin/news", response_model=AnnouncementAdminOut)
def create_announcement(
    title: str = Form(..., min_length=1, max_length=255),
    body: str = Form(..., min_length=1),
    game_slug: str = Form(..., min_length=1),
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

    game = _resolve_game_for_staff(db, staff, game_slug)
    image_path = _save_uploaded_image(image) if image and image.filename else None

    default_action = "save_draft" if staff.role == "captain" else "publish"
    action = _coerce_workflow_action(workflow_action, default_action)
    if staff.role == "captain" and action in {"publish", "reject"}:
        raise HTTPException(status_code=403, detail="Captains cannot publish or reject announcements")

    announcement = EsportsAnnouncement(
        title=clean_title,
        body=clean_body,
        image_path=image_path,
        game_id=game.id,
        created_by_admin_id=staff.user_id,
    )
    _set_workflow_state(announcement, staff, action)

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    row = _fetch_admin_announcement(db, announcement.id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username, row_game_slug, row_game_name = row
    return _serialize_admin(
        item,
        creator_username,
        approver_username,
        row_game_slug,
        row_game_name,
    )


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
        query = query.filter(EsportsAnnouncement.game_id.in_(tuple(staff.allowed_game_ids)))

    rows = (
        query.order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .limit(limit)
        .all()
    )
    return [
        _serialize_admin(item, creator_username, approver_username, game_slug, game_name)
        for item, creator_username, approver_username, game_slug, game_name in rows
    ]


@router.get("/admin/news/{announcement_id}", response_model=AnnouncementAdminOut)
def get_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username, game_slug, game_name = row
    _ensure_announcement_scope(staff, item)
    return _serialize_admin(item, creator_username, approver_username, game_slug, game_name)


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
    announcement, _creator_username, _approver_username, _game_slug, _game_name = row

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
    item, creator_username, approver_username, game_slug, game_name = updated
    return _serialize_admin(item, creator_username, approver_username, game_slug, game_name)


@router.post("/admin/news/{announcement_id}/submit", response_model=AnnouncementAdminOut)
def submit_announcement_for_approval(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username, _game_slug, _game_name = row

    _ensure_announcement_scope(staff, announcement)
    _ensure_can_edit(staff, announcement)
    _set_workflow_state(announcement, staff, "submit_for_approval")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username, game_slug, game_name = updated
    return _serialize_admin(item, creator_username, approver_username, game_slug, game_name)


@router.post("/admin/news/{announcement_id}/publish", response_model=AnnouncementAdminOut)
def publish_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username, _game_slug, _game_name = row

    _ensure_announcement_scope(staff, announcement)
    _set_workflow_state(announcement, staff, "publish")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username, game_slug, game_name = updated
    return _serialize_admin(item, creator_username, approver_username, game_slug, game_name)


@router.post("/admin/news/{announcement_id}/reject", response_model=AnnouncementAdminOut)
def reject_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_manager),
):
    row = _fetch_admin_announcement(db, announcement_id)
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement, _creator_username, _approver_username, _game_slug, _game_name = row

    _ensure_announcement_scope(staff, announcement)
    _set_workflow_state(announcement, staff, "reject")
    db.commit()
    db.refresh(announcement)

    updated = _fetch_admin_announcement(db, announcement_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, creator_username, approver_username, game_slug, game_name = updated
    return _serialize_admin(item, creator_username, approver_username, game_slug, game_name)


@router.get("/news/latest", response_model=AnnouncementPublicOut | None)
def get_latest_announcement(db: Session = Depends(get_db)):
    row = (
        db.query(EsportsAnnouncement, Game.slug, Game.name)
        .outerjoin(Game, Game.id == EsportsAnnouncement.game_id)
        .filter(EsportsAnnouncement.state == "published")
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .first()
    )
    if not row:
        return None
    item, game_slug, game_name = row
    return _serialize_public(item, game_slug, game_name)


@router.get("/news/archive", response_model=list[AnnouncementPublicOut])
def list_archive_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EsportsAnnouncement, Game.slug, Game.name)
        .outerjoin(Game, Game.id == EsportsAnnouncement.game_id)
        .filter(EsportsAnnouncement.state == "published")
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .offset(1)
        .limit(limit)
        .all()
    )
    return [_serialize_public(item, game_slug, game_name) for item, game_slug, game_name in rows]


@router.get("/news", response_model=list[AnnouncementPublicOut])
def list_public_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EsportsAnnouncement, Game.slug, Game.name)
        .outerjoin(Game, Game.id == EsportsAnnouncement.game_id)
        .filter(EsportsAnnouncement.state == "published")
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_public(item, game_slug, game_name) for item, game_slug, game_name in rows]


@router.get("/news/{announcement_id}", response_model=AnnouncementPublicOut)
def get_announcement_public(
    announcement_id: int,
    db: Session = Depends(get_db),
):
    row = (
        db.query(EsportsAnnouncement, Game.slug, Game.name)
        .outerjoin(Game, Game.id == EsportsAnnouncement.game_id)
        .filter(
            EsportsAnnouncement.id == announcement_id,
            EsportsAnnouncement.state == "published",
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, game_slug, game_name = row
    return _serialize_public(item, game_slug, game_name)


@router.delete("/admin/news/{announcement_id}")
def delete_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_announcement_deleter),
):
    item = (
        db.query(EsportsAnnouncement)
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
