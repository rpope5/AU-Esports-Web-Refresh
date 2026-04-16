import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import (
    StaffPrincipal,
    get_db,
    require_roster_deleter,
    require_roster_manager,
    require_roster_viewer,
)
from app.core.uploads import ImageUploadConfig, delete_uploaded_image, save_uploaded_image
from app.models.roster import Player
from app.schemas.roster import PlayerOut

router = APIRouter()

API_ROOT = Path(__file__).resolve().parents[3]
ROSTER_HEADSHOT_UPLOAD = ImageUploadConfig(
    upload_dir=API_ROOT / "uploads" / "roster",
    public_prefix="/uploads/roster",
    max_upload_bytes=int(os.getenv("ROSTER_HEADSHOT_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
    non_image_error_detail="Uploaded headshot must be an image",
    file_size_subject="Headshot",
)


def _normalize_optional(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    return normalized if normalized else None


def _require_non_empty(raw_value: str, field_name: str) -> str:
    normalized = raw_value.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return normalized


def _save_uploaded_headshot(upload: UploadFile) -> str:
    return save_uploaded_image(upload, ROSTER_HEADSHOT_UPLOAD)


def _delete_uploaded_headshot(image_path: str | None) -> bool:
    return delete_uploaded_image(image_path, ROSTER_HEADSHOT_UPLOAD)


@router.get("/roster", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    return db.query(Player).order_by(Player.game.asc(), Player.name.asc(), Player.id.asc()).all()


@router.get("/admin/roster", response_model=list[PlayerOut])
def list_players_admin(
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_viewer),
):
    return db.query(Player).order_by(Player.game.asc(), Player.name.asc(), Player.id.asc()).all()


@router.post("/admin/roster", response_model=PlayerOut, status_code=status.HTTP_201_CREATED)
def create_player_admin(
    name: str = Form(...),
    gamertag: str = Form(...),
    game: str = Form(...),
    role: str | None = Form(default=None),
    rank: str | None = Form(default=None),
    year: str | None = Form(default=None),
    major: str | None = Form(default=None),
    headshot_url: str | None = Form(default=None),
    headshot: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_manager),
):
    image_path = _normalize_optional(headshot_url)
    if headshot and headshot.filename:
        image_path = _save_uploaded_headshot(headshot)

    player = Player(
        name=_require_non_empty(name, "name"),
        gamertag=_require_non_empty(gamertag, "gamertag"),
        game=_require_non_empty(game, "game"),
        role=_normalize_optional(role),
        rank=_normalize_optional(rank),
        year=_normalize_optional(year),
        major=_normalize_optional(major),
        headshot=image_path,
    )

    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.patch("/admin/roster/{player_id}", response_model=PlayerOut)
def update_player_admin(
    player_id: int,
    name: str | None = Form(default=None),
    gamertag: str | None = Form(default=None),
    game: str | None = Form(default=None),
    role: str | None = Form(default=None),
    rank: str | None = Form(default=None),
    year: str | None = Form(default=None),
    major: str | None = Form(default=None),
    headshot_url: str | None = Form(default=None),
    remove_headshot: bool = Form(default=False),
    headshot: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_manager),
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    has_update = False

    if name is not None:
        player.name = _require_non_empty(name, "name")
        has_update = True
    if gamertag is not None:
        player.gamertag = _require_non_empty(gamertag, "gamertag")
        has_update = True
    if game is not None:
        player.game = _require_non_empty(game, "game")
        has_update = True
    if role is not None:
        player.role = _normalize_optional(role)
        has_update = True
    if rank is not None:
        player.rank = _normalize_optional(rank)
        has_update = True
    if year is not None:
        player.year = _normalize_optional(year)
        has_update = True
    if major is not None:
        player.major = _normalize_optional(major)
        has_update = True

    current_headshot = player.headshot
    if remove_headshot:
        _delete_uploaded_headshot(current_headshot)
        player.headshot = None
        current_headshot = None
        has_update = True

    if headshot_url is not None:
        next_headshot = _normalize_optional(headshot_url)
        if next_headshot != current_headshot:
            _delete_uploaded_headshot(current_headshot)
            player.headshot = next_headshot
            current_headshot = next_headshot
        has_update = True

    if headshot and headshot.filename:
        uploaded_path = _save_uploaded_headshot(headshot)
        _delete_uploaded_headshot(current_headshot)
        player.headshot = uploaded_path
        has_update = True

    if not has_update:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    db.commit()
    db.refresh(player)
    return player


@router.delete("/admin/roster/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_admin(
    player_id: int,
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_deleter),
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    headshot_path = player.headshot
    db.delete(player)
    db.commit()
    _delete_uploaded_headshot(headshot_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
