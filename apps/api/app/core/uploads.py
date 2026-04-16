from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CONTENT_TYPE_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@dataclass(frozen=True)
class ImageUploadConfig:
    upload_dir: Path
    public_prefix: str
    max_upload_bytes: int
    non_image_error_detail: str
    file_size_subject: str


def _parse_image_extension(upload: UploadFile, non_image_error_detail: str) -> str:
    content_type = (upload.content_type or "").lower().strip()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=non_image_error_detail)

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


def save_uploaded_image(upload: UploadFile, config: ImageUploadConfig) -> str:
    ext = _parse_image_extension(upload, config.non_image_error_detail)
    config.upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{ext}"
    destination = config.upload_dir / filename

    total_written = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > config.max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"{config.file_size_subject} exceeds max size "
                            f"of {config.max_upload_bytes} bytes"
                        ),
                    )
                output.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        upload.file.close()

    normalized_prefix = config.public_prefix.rstrip("/")
    return f"{normalized_prefix}/{filename}"


def delete_uploaded_image(image_path: str | None, config: ImageUploadConfig) -> bool:
    if not image_path:
        return False

    normalized_path = image_path.strip()
    normalized_prefix = config.public_prefix.rstrip("/")
    prefix_with_separator = f"{normalized_prefix}/"
    if not normalized_path.startswith(prefix_with_separator):
        return False

    relative_path = normalized_path[len(prefix_with_separator) :]
    if not relative_path:
        return False

    upload_dir_resolved = config.upload_dir.resolve()
    candidate = (upload_dir_resolved / relative_path).resolve()

    try:
        candidate.relative_to(upload_dir_resolved)
    except ValueError:
        return False

    if not candidate.exists() or not candidate.is_file():
        return False

    try:
        candidate.unlink()
        return True
    except OSError:
        return False
