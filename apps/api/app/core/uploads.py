from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import HTTPException, UploadFile

from app.core.config import get_settings

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
    blob_prefix: str
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
    settings = get_settings()

    try:
        if settings.media_backend == "azure_blob":
            return _save_uploaded_image_blob(upload, config, ext)
        return _save_uploaded_image_local(upload, config, ext)
    finally:
        upload.file.close()


def delete_uploaded_image(image_path: str | None, config: ImageUploadConfig) -> bool:
    if not image_path:
        return False

    normalized_path = image_path.strip()
    settings = get_settings()

    # Always allow deleting legacy local uploads by /uploads path.
    if normalized_path.startswith("/uploads/"):
        return _delete_uploaded_image_local(normalized_path, config)

    if settings.media_backend == "azure_blob":
        return _delete_uploaded_image_blob(normalized_path, config)

    return _delete_uploaded_image_local(normalized_path, config)


def _read_upload_bytes(upload: UploadFile, config: ImageUploadConfig) -> bytes:
    content = bytearray()
    total_written = 0
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
        content.extend(chunk)
    return bytes(content)


def _save_uploaded_image_local(upload: UploadFile, config: ImageUploadConfig, ext: str) -> str:
    config.upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{ext}"
    destination = config.upload_dir / filename

    try:
        with destination.open("wb") as output:
            output.write(_read_upload_bytes(upload, config))
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise

    normalized_prefix = config.public_prefix.rstrip("/")
    return f"{normalized_prefix}/{filename}"


def _save_uploaded_image_blob(upload: UploadFile, config: ImageUploadConfig, ext: str) -> str:
    settings = get_settings()
    connection_string = (settings.media_azure_blob_connection_string or "").strip()
    if not connection_string:
        raise HTTPException(
            status_code=500,
            detail="MEDIA_BACKEND is azure_blob but MEDIA_AZURE_BLOB_CONNECTION_STRING is missing",
        )

    normalized_prefix = config.blob_prefix.strip("/")
    blob_name = f"{normalized_prefix}/{uuid4().hex}{ext}" if normalized_prefix else f"{uuid4().hex}{ext}"
    container_name = settings.media_azure_blob_container.strip()

    try:
        service = BlobServiceClient.from_connection_string(connection_string)
        container_client = service.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            _read_upload_bytes(upload, config),
            overwrite=False,
            content_settings=ContentSettings(
                content_type=(upload.content_type or "application/octet-stream"),
            ),
        )
        return blob_client.url
    except HTTPException:
        raise
    except AzureError as exc:
        raise HTTPException(status_code=500, detail="Failed to store uploaded image") from exc


def _delete_uploaded_image_local(normalized_path: str, config: ImageUploadConfig) -> bool:
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


def _delete_uploaded_image_blob(normalized_path: str, config: ImageUploadConfig) -> bool:
    settings = get_settings()
    connection_string = (settings.media_azure_blob_connection_string or "").strip()
    container_name = settings.media_azure_blob_container.strip()
    if not connection_string or not container_name:
        return False

    blob_name = _extract_blob_name(normalized_path, container_name)
    if not blob_name:
        return False

    normalized_blob_prefix = config.blob_prefix.strip("/")
    if normalized_blob_prefix and not blob_name.startswith(f"{normalized_blob_prefix}/"):
        return False

    try:
        service = BlobServiceClient.from_connection_string(connection_string)
        container_client = service.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob(delete_snapshots="include")
        return True
    except ResourceNotFoundError:
        return False
    except AzureError:
        return False


def _extract_blob_name(image_path: str, container_name: str) -> str | None:
    parsed = urlparse(image_path)

    if parsed.scheme and parsed.netloc:
        normalized_path = parsed.path.lstrip("/")
        container_prefix = f"{container_name}/"
        if normalized_path.startswith(container_prefix):
            return normalized_path[len(container_prefix) :]
        return None

    normalized_path = image_path.lstrip("/")
    if normalized_path.startswith(f"{container_name}/"):
        return normalized_path[len(container_name) + 1 :]

    return normalized_path or None
