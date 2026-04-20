import os
import json
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import get_settings
from app.core.deps import (
    StaffPrincipal,
    get_db,
    require_roster_deleter,
    require_roster_manager,
    require_roster_viewer,
)
from app.core.uploads import ImageUploadConfig, delete_uploaded_image, save_uploaded_image
from app.models.game import Game
from app.models.roster import Player
from app.schemas.roster import GameOptionOut, PlayerOut

router = APIRouter()

settings = get_settings()
ROSTER_HEADSHOT_UPLOAD = ImageUploadConfig(
    upload_dir=settings.uploads_root_path / "roster",
    public_prefix="/uploads/roster",
    blob_prefix="roster",
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


def _normalize_game_key(raw_value: str | None) -> str:
    normalized = (raw_value or "").strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


LEGACY_GAME_KEY_TO_SLUG: dict[str, str] = {
    "valorant": "valorant",
    "counter strike 2": "cs2",
    "counter strike2": "cs2",
    "counter strike": "cs2",
    "cs2": "cs2",
    "csgo": "cs2",
    "fortnite": "fortnite",
    "rainbow six siege": "r6",
    "tom clancy s rainbow six siege": "r6",
    "r6": "r6",
    "r6 siege": "r6",
    "rocket league": "rocket-league",
    "rocketleague": "rocket-league",
    "overwatch": "overwatch",
    "call of duty": "cod",
    "callofduty": "cod",
    "cod": "cod",
    "hearthstone": "hearthstone",
    "super smash bros ultimate": "smash",
    "super smash bros": "smash",
    "smash": "smash",
    "mario kart": "mario-kart",
    "mariokart": "mario-kart",
}


def _list_games(db: Session) -> list[Game]:
    return db.query(Game).order_by(Game.name.asc(), Game.slug.asc()).all()


def _games_by_slug(db: Session) -> dict[str, Game]:
    return {game.slug: game for game in _list_games(db)}


def _resolve_legacy_primary_slug(raw_game: str, games_by_slug: dict[str, Game]) -> str | None:
    direct_slug = raw_game.strip().lower()
    if direct_slug in games_by_slug:
        return direct_slug

    normalized = _normalize_game_key(raw_game)
    if not normalized:
        return None

    mapped = LEGACY_GAME_KEY_TO_SLUG.get(normalized)
    if mapped and mapped in games_by_slug:
        return mapped

    for slug, game in games_by_slug.items():
        if _normalize_game_key(game.name) == normalized:
            return slug

    return None


def _resolve_primary_slug(
    *,
    primary_game_slug: str | None,
    legacy_game: str | None,
    games_by_slug: dict[str, Game],
    required: bool,
) -> str | None:
    if primary_game_slug is not None:
        normalized = primary_game_slug.strip().lower()
        if not normalized:
            raise HTTPException(status_code=400, detail="primary_game_slug is required")
        return normalized

    if legacy_game is not None:
        if not legacy_game.strip():
            raise HTTPException(status_code=400, detail="game is required")
        mapped = _resolve_legacy_primary_slug(legacy_game, games_by_slug)
        if mapped:
            return mapped
        raise HTTPException(status_code=400, detail="game must map to a canonical game slug")

    if required:
        raise HTTPException(status_code=400, detail="primary_game_slug is required")
    return None


def _parse_secondary_game_slugs(raw_secondary: str | None) -> list[str] | None:
    if raw_secondary is None:
        return None

    text_value = raw_secondary.strip()
    if not text_value:
        return []

    try:
        parsed: object = json.loads(text_value)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in text_value.split(",") if item.strip()]

    if isinstance(parsed, str):
        parsed = [parsed]

    if not isinstance(parsed, list):
        raise HTTPException(status_code=400, detail="secondary_game_slugs must be a JSON array or CSV string")

    cleaned: list[str] = []
    for value in parsed:
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail="secondary_game_slugs must contain only string slugs")
        normalized = value.strip().lower()
        if normalized:
            cleaned.append(normalized)
    return cleaned


def _validate_game_selection(
    *,
    primary_slug: str,
    secondary_slugs: list[str],
    games_by_slug: dict[str, Game],
) -> tuple[Game, list[Game]]:
    primary_game = games_by_slug.get(primary_slug)
    if not primary_game:
        raise HTTPException(status_code=400, detail=f"Unknown primary game slug: {primary_slug}")

    seen: set[str] = set()
    ordered_secondary: list[str] = []
    for slug in secondary_slugs:
        if slug in seen:
            raise HTTPException(status_code=400, detail="secondary_game_slugs cannot contain duplicates")
        if slug == primary_slug:
            raise HTTPException(
                status_code=400,
                detail="secondary_game_slugs cannot include the primary_game_slug",
            )
        if slug not in games_by_slug:
            raise HTTPException(status_code=400, detail=f"Unknown secondary game slug: {slug}")
        seen.add(slug)
        ordered_secondary.append(slug)

    return primary_game, [games_by_slug[slug] for slug in ordered_secondary]


def _list_players(db: Session) -> list[Player]:
    players = (
        db.query(Player)
        .options(
            joinedload(Player.primary_game),
            selectinload(Player.secondary_games),
        )
        .all()
    )
    players.sort(
        key=lambda player: (
            (player.primary_game_name or player.game or "").lower(),
            (player.name or "").lower(),
            int(player.id or 0),
        )
    )
    return players


@router.get("/games", response_model=list[GameOptionOut])
def list_games(db: Session = Depends(get_db)):
    return _list_games(db)


@router.get("/roster", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    return _list_players(db)


@router.get("/admin/roster", response_model=list[PlayerOut])
def list_players_admin(
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_viewer),
):
    return _list_players(db)


@router.post("/admin/roster", response_model=PlayerOut, status_code=status.HTTP_201_CREATED)
def create_player_admin(
    name: str = Form(...),
    gamertag: str = Form(...),
    primary_game_slug: str | None = Form(default=None),
    game: str | None = Form(default=None),
    secondary_game_slugs: str | None = Form(default=None),
    role: str | None = Form(default=None),
    rank: str | None = Form(default=None),
    year: str | None = Form(default=None),
    major: str | None = Form(default=None),
    headshot_url: str | None = Form(default=None),
    headshot: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _staff: StaffPrincipal = Depends(require_roster_manager),
):
    games_by_slug = _games_by_slug(db)
    resolved_primary_slug = _resolve_primary_slug(
        primary_game_slug=primary_game_slug,
        legacy_game=game,
        games_by_slug=games_by_slug,
        required=True,
    )
    parsed_secondary_slugs = _parse_secondary_game_slugs(secondary_game_slugs) or []
    primary_game, secondary_games = _validate_game_selection(
        primary_slug=resolved_primary_slug,
        secondary_slugs=parsed_secondary_slugs,
        games_by_slug=games_by_slug,
    )

    image_path = _normalize_optional(headshot_url)
    if headshot and headshot.filename:
        image_path = _save_uploaded_headshot(headshot)

    player = Player(
        name=_require_non_empty(name, "name"),
        gamertag=_require_non_empty(gamertag, "gamertag"),
        game=primary_game.name,
        primary_game_id=primary_game.id,
        role=_normalize_optional(role),
        rank=_normalize_optional(rank),
        year=_normalize_optional(year),
        major=_normalize_optional(major),
        headshot=image_path,
    )
    player.secondary_games = secondary_games

    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.patch("/admin/roster/{player_id}", response_model=PlayerOut)
def update_player_admin(
    player_id: int,
    name: str | None = Form(default=None),
    gamertag: str | None = Form(default=None),
    primary_game_slug: str | None = Form(default=None),
    game: str | None = Form(default=None),
    secondary_game_slugs: str | None = Form(default=None),
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

    games_by_slug = _games_by_slug(db)
    resolved_primary_slug = _resolve_primary_slug(
        primary_game_slug=primary_game_slug,
        legacy_game=game,
        games_by_slug=games_by_slug,
        required=False,
    )
    parsed_secondary_slugs = _parse_secondary_game_slugs(secondary_game_slugs)

    has_update = False
    primary_updated = False

    if name is not None:
        player.name = _require_non_empty(name, "name")
        has_update = True
    if gamertag is not None:
        player.gamertag = _require_non_empty(gamertag, "gamertag")
        has_update = True
    if resolved_primary_slug is not None:
        primary_game, _secondary_games = _validate_game_selection(
            primary_slug=resolved_primary_slug,
            secondary_slugs=[],
            games_by_slug=games_by_slug,
        )
        player.primary_game_id = primary_game.id
        player.game = primary_game.name
        primary_updated = True
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

    if parsed_secondary_slugs is not None:
        base_primary_slug = player.primary_game_slug
        if not base_primary_slug:
            raise HTTPException(status_code=400, detail="A primary game must be selected before secondary games")

        _, secondary_games = _validate_game_selection(
            primary_slug=base_primary_slug,
            secondary_slugs=parsed_secondary_slugs,
            games_by_slug=games_by_slug,
        )
        player.secondary_games = secondary_games
        has_update = True
    elif primary_updated:
        base_primary_slug = player.primary_game_slug
        if base_primary_slug:
            existing_secondary = [slug for slug in player.secondary_game_slugs if slug != base_primary_slug]
            _, secondary_games = _validate_game_selection(
                primary_slug=base_primary_slug,
                secondary_slugs=existing_secondary,
                games_by_slug=games_by_slug,
            )
            player.secondary_games = secondary_games

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
