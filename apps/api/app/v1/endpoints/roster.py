import os
import json
import re
from dataclasses import dataclass

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
from app.models.roster import Player, PlayerGameProfile
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


@dataclass
class ValidatedGameProfile:
    game: Game
    role: str | None
    rank: str | None
    is_primary: bool


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


def _parse_game_profiles(raw_profiles: str | None) -> list[dict[str, object]] | None:
    if raw_profiles is None:
        return None

    text_value = raw_profiles.strip()
    if not text_value:
        return []

    try:
        parsed: object = json.loads(text_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="game_profiles must be a valid JSON array") from exc

    if not isinstance(parsed, list):
        raise HTTPException(status_code=400, detail="game_profiles must be a JSON array")

    normalized_profiles: list[dict[str, object]] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Each game profile must be an object")

        raw_slug = item.get("game_slug")
        if not isinstance(raw_slug, str) or not raw_slug.strip():
            raise HTTPException(status_code=400, detail="Each game profile must include game_slug")

        raw_role = item.get("role")
        if raw_role is not None and not isinstance(raw_role, str):
            raise HTTPException(status_code=400, detail="game profile role must be a string or null")

        raw_rank = item.get("rank")
        if raw_rank is not None and not isinstance(raw_rank, str):
            raise HTTPException(status_code=400, detail="game profile rank must be a string or null")

        raw_is_primary = item.get("is_primary", False)
        if not isinstance(raw_is_primary, bool):
            raise HTTPException(status_code=400, detail="game profile is_primary must be a boolean")

        normalized_profiles.append(
            {
                "game_slug": raw_slug.strip().lower(),
                "role": _normalize_optional(raw_role),
                "rank": _normalize_optional(raw_rank),
                "is_primary": raw_is_primary,
            }
        )

    return normalized_profiles


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


def _validate_game_profiles(
    *,
    parsed_profiles: list[dict[str, object]],
    games_by_slug: dict[str, Game],
    required: bool,
) -> list[ValidatedGameProfile]:
    if len(parsed_profiles) == 0:
        if required:
            raise HTTPException(status_code=400, detail="At least one game profile is required")
        return []

    seen: set[str] = set()
    normalized: list[ValidatedGameProfile] = []
    for item in parsed_profiles:
        slug = item["game_slug"]
        if not isinstance(slug, str):
            raise HTTPException(status_code=400, detail="Each game profile must include game_slug")
        if slug in seen:
            raise HTTPException(status_code=400, detail="game_profiles cannot contain duplicate game_slug values")

        game = games_by_slug.get(slug)
        if not game:
            raise HTTPException(status_code=400, detail=f"Unknown game slug in game_profiles: {slug}")

        seen.add(slug)
        normalized.append(
            ValidatedGameProfile(
                game=game,
                role=item["role"] if isinstance(item["role"], str) or item["role"] is None else None,
                rank=item["rank"] if isinstance(item["rank"], str) or item["rank"] is None else None,
                is_primary=bool(item["is_primary"]),
            )
        )

    primary_index = next((index for index, profile in enumerate(normalized) if profile.is_primary), 0)
    finalized: list[ValidatedGameProfile] = []
    for index, profile in enumerate(normalized):
        finalized.append(
            ValidatedGameProfile(
                game=profile.game,
                role=profile.role,
                rank=profile.rank,
                is_primary=index == primary_index,
            )
        )

    return finalized


def _build_game_profiles_from_legacy(
    *,
    primary_slug: str,
    secondary_slugs: list[str],
    shared_role: str | None,
    shared_rank: str | None,
    games_by_slug: dict[str, Game],
) -> list[ValidatedGameProfile]:
    primary_game, secondary_games = _validate_game_selection(
        primary_slug=primary_slug,
        secondary_slugs=secondary_slugs,
        games_by_slug=games_by_slug,
    )

    profiles: list[ValidatedGameProfile] = [
        ValidatedGameProfile(
            game=primary_game,
            role=shared_role,
            rank=shared_rank,
            is_primary=True,
        )
    ]
    profiles.extend(
        ValidatedGameProfile(
            game=game,
            role=shared_role,
            rank=shared_rank,
            is_primary=False,
        )
        for game in secondary_games
    )
    return profiles


def _apply_game_profiles_to_player(player: Player, profiles: list[ValidatedGameProfile]) -> None:
    if len(profiles) == 0:
        raise HTTPException(status_code=400, detail="At least one game profile is required")

    player.game_profiles = [
        PlayerGameProfile(
            game_id=profile.game.id,
            role=profile.role,
            rank=profile.rank,
            is_primary=profile.is_primary,
        )
        for profile in profiles
    ]

    primary_profile = next((profile for profile in profiles if profile.is_primary), profiles[0])
    player.primary_game_id = primary_profile.game.id
    player.game = primary_profile.game.name
    player.role = primary_profile.role
    player.rank = primary_profile.rank
    player.secondary_games = [profile.game for profile in profiles if not profile.is_primary]


def _list_players(db: Session) -> list[Player]:
    players = (
        db.query(Player)
        .options(
            joinedload(Player.primary_game),
            selectinload(Player.secondary_games),
            selectinload(Player.game_profiles).joinedload(PlayerGameProfile.game),
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
    game_profiles: str | None = Form(default=None),
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
    parsed_game_profiles = _parse_game_profiles(game_profiles)
    if parsed_game_profiles is not None:
        validated_profiles = _validate_game_profiles(
            parsed_profiles=parsed_game_profiles,
            games_by_slug=games_by_slug,
            required=True,
        )
    else:
        resolved_primary_slug = _resolve_primary_slug(
            primary_game_slug=primary_game_slug,
            legacy_game=game,
            games_by_slug=games_by_slug,
            required=True,
        )
        parsed_secondary_slugs = _parse_secondary_game_slugs(secondary_game_slugs) or []
        validated_profiles = _build_game_profiles_from_legacy(
            primary_slug=resolved_primary_slug,
            secondary_slugs=parsed_secondary_slugs,
            shared_role=_normalize_optional(role),
            shared_rank=_normalize_optional(rank),
            games_by_slug=games_by_slug,
        )

    image_path = _normalize_optional(headshot_url)
    if headshot and headshot.filename:
        image_path = _save_uploaded_headshot(headshot)

    player = Player(
        name=_require_non_empty(name, "name"),
        gamertag=_require_non_empty(gamertag, "gamertag"),
        game=validated_profiles[0].game.name,
        primary_game_id=validated_profiles[0].game.id,
        role=validated_profiles[0].role,
        rank=validated_profiles[0].rank,
        year=_normalize_optional(year),
        major=_normalize_optional(major),
        headshot=image_path,
    )
    _apply_game_profiles_to_player(player, validated_profiles)

    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.patch("/admin/roster/{player_id}", response_model=PlayerOut)
def update_player_admin(
    player_id: int,
    name: str | None = Form(default=None),
    gamertag: str | None = Form(default=None),
    game_profiles: str | None = Form(default=None),
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
    parsed_game_profiles = _parse_game_profiles(game_profiles)
    resolved_primary_slug = _resolve_primary_slug(
        primary_game_slug=primary_game_slug,
        legacy_game=game,
        games_by_slug=games_by_slug,
        required=False,
    )
    parsed_secondary_slugs = _parse_secondary_game_slugs(secondary_game_slugs)

    has_update = False
    primary_updated = False
    game_profiles_updated = False

    if name is not None:
        player.name = _require_non_empty(name, "name")
        has_update = True
    if gamertag is not None:
        player.gamertag = _require_non_empty(gamertag, "gamertag")
        has_update = True
    if parsed_game_profiles is not None:
        validated_profiles = _validate_game_profiles(
            parsed_profiles=parsed_game_profiles,
            games_by_slug=games_by_slug,
            required=True,
        )
        _apply_game_profiles_to_player(player, validated_profiles)
        game_profiles_updated = True
        has_update = True
    elif resolved_primary_slug is not None:
        primary_game, _secondary_games = _validate_game_selection(
            primary_slug=resolved_primary_slug,
            secondary_slugs=[],
            games_by_slug=games_by_slug,
        )
        player.primary_game_id = primary_game.id
        player.game = primary_game.name
        primary_updated = True
        has_update = True
    if parsed_game_profiles is None and role is not None:
        player.role = _normalize_optional(role)
        has_update = True
    if parsed_game_profiles is None and rank is not None:
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

    if parsed_game_profiles is None and parsed_secondary_slugs is not None:
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
    elif parsed_game_profiles is None and primary_updated:
        base_primary_slug = player.primary_game_slug
        if base_primary_slug:
            existing_secondary = [slug for slug in player.secondary_game_slugs if slug != base_primary_slug]
            _, secondary_games = _validate_game_selection(
                primary_slug=base_primary_slug,
                secondary_slugs=existing_secondary,
                games_by_slug=games_by_slug,
            )
            player.secondary_games = secondary_games

    if parsed_game_profiles is None and (primary_updated or parsed_secondary_slugs is not None or role is not None or rank is not None):
        base_primary_slug = player.primary_game_slug
        if not base_primary_slug:
            raise HTTPException(status_code=400, detail="A primary game must be selected before configuring game profiles")

        secondary_slugs_for_profiles = player.secondary_game_slugs
        legacy_profiles = _build_game_profiles_from_legacy(
            primary_slug=base_primary_slug,
            secondary_slugs=secondary_slugs_for_profiles,
            shared_role=player.role,
            shared_rank=player.rank,
            games_by_slug=games_by_slug,
        )
        _apply_game_profiles_to_player(player, legacy_profiles)
        game_profiles_updated = True
        has_update = True

    if parsed_game_profiles is None and not game_profiles_updated and len(player.game_profiles) == 0:
        base_primary_slug = player.primary_game_slug
        if base_primary_slug:
            legacy_profiles = _build_game_profiles_from_legacy(
                primary_slug=base_primary_slug,
                secondary_slugs=player.secondary_game_slugs,
                shared_role=player.role,
                shared_rank=player.rank,
                games_by_slug=games_by_slug,
            )
            _apply_game_profiles_to_player(player, legacy_profiles)

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
