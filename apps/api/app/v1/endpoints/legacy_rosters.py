from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import StaffPrincipal, get_db, require_roster_manager
from app.models.legacy_roster import LegacyRoster, LegacyRosterPlayer, LegacyRosterPlayerGameProfile
from app.models.roster import Player, PlayerGameProfile
from app.schemas.legacy_roster import (
    LegacyRosterCreateRequest,
    LegacyRosterDetailOut,
    LegacyRosterListItemOut,
)

router = APIRouter()

NON_MEANINGFUL_RANK_VALUES = {"na", "n/a"}


def _normalize_optional(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    return normalized if normalized else None


def _normalize_optional_rank(raw_value: str | None) -> str | None:
    normalized = _normalize_optional(raw_value)
    if normalized is None:
        return None
    return None if normalized.lower() in NON_MEANINGFUL_RANK_VALUES else normalized


def _slugify_legacy_roster_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def _list_current_players_for_snapshot(db: Session) -> list[Player]:
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


def _legacy_roster_query(db: Session):
    return db.query(LegacyRoster).options(
        selectinload(LegacyRoster.players).selectinload(LegacyRosterPlayer.game_profiles)
    )


def _find_legacy_roster(db: Session, id_or_slug: str) -> LegacyRoster | None:
    query = _legacy_roster_query(db)
    if id_or_slug.isdigit():
        by_id = query.filter(LegacyRoster.id == int(id_or_slug)).first()
        if by_id:
            return by_id
    return query.filter(LegacyRoster.slug == id_or_slug.strip().lower()).first()


def _build_snapshot_profiles(player: Player) -> list[dict[str, object]]:
    profiles: list[dict[str, object]] = []

    for profile in player.game_profiles or []:
        game_slug = profile.game_slug
        game_name = profile.game_name
        if not game_slug or not game_name:
            continue
        profiles.append(
            {
                "original_game_id": profile.game_id,
                "game_slug": game_slug,
                "game_name": game_name,
                "role": _normalize_optional(profile.role),
                "rank": _normalize_optional_rank(profile.rank),
                "is_primary": bool(profile.is_primary),
            }
        )

    if len(profiles) == 0:
        primary_slug = player.primary_game_slug
        primary_name = player.primary_game_name or player.game
        if primary_slug and primary_name:
            profiles.append(
                {
                    "original_game_id": player.primary_game_id,
                    "game_slug": primary_slug,
                    "game_name": primary_name,
                    "role": _normalize_optional(player.role),
                    "rank": _normalize_optional_rank(player.rank),
                    "is_primary": True,
                }
            )

    if len(profiles) == 0:
        return []

    primary_index = next((index for index, row in enumerate(profiles) if bool(row["is_primary"])), 0)
    return [{**row, "is_primary": index == primary_index} for index, row in enumerate(profiles)]


def _ensure_admin_actor_for_delete(staff: StaffPrincipal) -> None:
    if staff.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/legacy-rosters", response_model=list[LegacyRosterListItemOut])
def list_legacy_rosters(db: Session = Depends(get_db)):
    items = (
        _legacy_roster_query(db)
        .order_by(LegacyRoster.created_at.desc(), LegacyRoster.id.desc())
        .all()
    )
    return items


@router.get("/legacy-rosters/{id_or_slug}", response_model=LegacyRosterDetailOut)
def get_legacy_roster(id_or_slug: str, db: Session = Depends(get_db)):
    legacy_roster = _find_legacy_roster(db, id_or_slug)
    if not legacy_roster:
        raise HTTPException(status_code=404, detail="Legacy roster not found")
    return legacy_roster


@router.post("/admin/legacy-rosters", response_model=LegacyRosterDetailOut, status_code=status.HTTP_201_CREATED)
def create_legacy_roster_snapshot(
    payload: LegacyRosterCreateRequest,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_roster_manager),
):
    snapshot_name = payload.name.strip()
    if not snapshot_name:
        raise HTTPException(status_code=400, detail="name is required")

    snapshot_slug = _slugify_legacy_roster_name(snapshot_name)
    if not snapshot_slug:
        raise HTTPException(status_code=400, detail="name must include letters or numbers")

    duplicate = (
        db.query(LegacyRoster.id)
        .filter(
            or_(
                func.lower(LegacyRoster.name) == snapshot_name.lower(),
                LegacyRoster.slug == snapshot_slug,
            )
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A legacy roster with this name already exists")

    current_players = _list_current_players_for_snapshot(db)
    if len(current_players) == 0:
        raise HTTPException(status_code=400, detail="Cannot create legacy roster from an empty current roster")

    legacy_roster = LegacyRoster(
        name=snapshot_name,
        slug=snapshot_slug,
        created_by_admin_id=staff.user_id,
    )
    db.add(legacy_roster)
    db.flush()

    for sort_order, player in enumerate(current_players):
        primary_name = player.primary_game_name or player.game or "Unknown Game"
        snapshot_player = LegacyRosterPlayer(
            legacy_roster_id=legacy_roster.id,
            original_player_id=player.id,
            name=player.name,
            gamertag=player.gamertag,
            game=primary_name,
            primary_game_slug=player.primary_game_slug,
            primary_game_name=primary_name,
            role=_normalize_optional(player.primary_role),
            rank=_normalize_optional_rank(player.primary_rank),
            year=_normalize_optional(player.year),
            major=_normalize_optional(player.major),
            headshot=_normalize_optional(player.headshot),
            sort_order=sort_order,
        )
        db.add(snapshot_player)
        db.flush()

        snapshot_profiles = _build_snapshot_profiles(player)
        for row in snapshot_profiles:
            db.add(
                LegacyRosterPlayerGameProfile(
                    legacy_roster_player_id=snapshot_player.id,
                    original_game_id=row["original_game_id"] if isinstance(row["original_game_id"], int) else None,
                    game_slug=row["game_slug"] if isinstance(row["game_slug"], str) else "",
                    game_name=row["game_name"] if isinstance(row["game_name"], str) else "",
                    role=row["role"] if isinstance(row["role"], str) or row["role"] is None else None,
                    rank=row["rank"] if isinstance(row["rank"], str) or row["rank"] is None else None,
                    is_primary=bool(row["is_primary"]),
                )
            )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A legacy roster with this name already exists") from exc

    created = _find_legacy_roster(db, str(legacy_roster.id))
    if not created:
        raise HTTPException(status_code=500, detail="Legacy roster snapshot was created but could not be reloaded")
    return created


@router.delete("/admin/legacy-rosters/{id_or_slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_legacy_roster(
    id_or_slug: str,
    db: Session = Depends(get_db),
    staff: StaffPrincipal = Depends(require_roster_manager),
):
    _ensure_admin_actor_for_delete(staff)

    legacy_roster = _find_legacy_roster(db, id_or_slug)
    if not legacy_roster:
        raise HTTPException(status_code=404, detail="Legacy roster not found")

    db.delete(legacy_roster)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
