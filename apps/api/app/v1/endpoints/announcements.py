import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.announcement import EsportsAnnouncement
from app.schemas.announcement import AnnouncementAdminOut, AnnouncementPublicOut

router = APIRouter()

API_ROOT = Path(__file__).resolve().parents[3]
NEWS_UPLOAD_DIR = API_ROOT / "uploads" / "news"
MAX_UPLOAD_BYTES = int(os.getenv("NEWS_IMAGE_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CONTENT_TYPE_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_image_extension(upload: UploadFile) -> str:
    content_type = (upload.content_type or "").lower().strip()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    ext = Path(upload.filename or "").suffix.lower().strip()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return ext

    fallback_ext = CONTENT_TYPE_TO_EXTENSION.get(content_type)
    if fallback_ext:
        return fallback_ext

    allowed_list = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported image type. Allowed extensions: {allowed_list}",
    )


def _save_uploaded_image(upload: UploadFile) -> str:
    ext = _parse_image_extension(upload)
    NEWS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{ext}"
    destination = NEWS_UPLOAD_DIR / filename

    total_written = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Image exceeds max size of {MAX_UPLOAD_BYTES} bytes",
                    )
                output.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        upload.file.close()

    return f"/uploads/news/{filename}"


def _delete_uploaded_image(image_path: str | None) -> bool:
    if not image_path:
        return False

    normalized = image_path.strip()
    if not normalized.startswith("/uploads/news/"):
        return False

    news_dir_resolved = NEWS_UPLOAD_DIR.resolve()
    candidate = (API_ROOT / normalized.lstrip("/")).resolve()

    try:
        candidate.relative_to(news_dir_resolved)
    except ValueError:
        return False

    if not candidate.exists() or not candidate.is_file():
        return False

    try:
        candidate.unlink()
        return True
    except OSError:
        return False


def _serialize_public(item: EsportsAnnouncement) -> AnnouncementPublicOut:
    return AnnouncementPublicOut(
        id=item.id,
        title=item.title,
        body=item.body,
        image_url=item.image_path,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_admin(
    item: EsportsAnnouncement,
    created_by_username: str | None,
) -> AnnouncementAdminOut:
    return AnnouncementAdminOut(
        id=item.id,
        title=item.title,
        body=item.body,
        image_url=item.image_path,
        created_at=item.created_at,
        updated_at=item.updated_at,
        created_by_admin_id=item.created_by_admin_id,
        created_by_username=created_by_username,
    )


@router.post("/admin/news", response_model=AnnouncementAdminOut)
def create_announcement(
    title: str = Form(..., min_length=1, max_length=255),
    body: str = Form(..., min_length=1),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    clean_title = title.strip()
    clean_body = body.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not clean_body:
        raise HTTPException(status_code=400, detail="Body is required")

    image_path = None
    if image and image.filename:
        image_path = _save_uploaded_image(image)

    creator = None
    username = user.get("sub")
    if username:
        creator = db.query(AdminUser).filter(AdminUser.username == username).first()

    announcement = EsportsAnnouncement(
        title=clean_title,
        body=clean_body,
        image_path=image_path,
        created_by_admin_id=creator.id if creator else None,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return _serialize_admin(announcement, creator.username if creator else username)


@router.get("/admin/news", response_model=list[AnnouncementAdminOut])
def list_announcements_admin(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    rows = (
        db.query(EsportsAnnouncement, AdminUser.username)
        .outerjoin(AdminUser, AdminUser.id == EsportsAnnouncement.created_by_admin_id)
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_admin(item, username) for item, username in rows]


@router.get("/admin/news/{announcement_id}", response_model=AnnouncementAdminOut)
def get_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    row = (
        db.query(EsportsAnnouncement, AdminUser.username)
        .outerjoin(AdminUser, AdminUser.id == EsportsAnnouncement.created_by_admin_id)
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item, username = row
    return _serialize_admin(item, username)


@router.get("/news/latest", response_model=AnnouncementPublicOut | None)
def get_latest_announcement(db: Session = Depends(get_db)):
    item = (
        db.query(EsportsAnnouncement)
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .first()
    )
    if not item:
        return None
    return _serialize_public(item)


@router.get("/news/archive", response_model=list[AnnouncementPublicOut])
def list_archive_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EsportsAnnouncement)
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
        .offset(1)
        .limit(limit)
        .all()
    )
    return [_serialize_public(item) for item in rows]


@router.get("/news", response_model=list[AnnouncementPublicOut])
def list_public_announcements(
    limit: int = Query(default=25, ge=1, le=250),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(EsportsAnnouncement)
        .order_by(EsportsAnnouncement.created_at.desc(), EsportsAnnouncement.id.desc())
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
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return _serialize_public(item)


@router.delete("/admin/news/{announcement_id}")
def delete_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    item = (
        db.query(EsportsAnnouncement)
        .filter(EsportsAnnouncement.id == announcement_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    image_path = item.image_path
    db.delete(item)
    db.commit()

    image_deleted = _delete_uploaded_image(image_path)
    return {
        "message": "Announcement deleted",
        "id": announcement_id,
        "image_deleted": image_deleted,
    }
