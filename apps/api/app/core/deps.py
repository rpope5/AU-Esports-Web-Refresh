from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import false
from sqlalchemy.orm import Query, Session

from app.core.jwt_auth import decode_access_token
from app.core.roles import (
    PermissionName,
    StaffPermissions,
    StaffRole,
    normalize_staff_role,
    permissions_for_role,
    role_has_global_game_access,
)
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.recruit import RecruitGameProfile
from app.models.staff_game_access import StaffGameAccess

bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass(frozen=True)
class StaffPrincipal:
    user_id: int
    username: str
    role: StaffRole
    permissions: StaffPermissions
    has_global_game_access: bool
    allowed_game_ids: frozenset[int]
    allowed_game_slugs: frozenset[str]

    def can(self, permission: PermissionName) -> bool:
        return bool(getattr(self.permissions, permission))


def build_staff_principal(db: Session, user: AdminUser) -> StaffPrincipal:
    normalized_role = normalize_staff_role(user.role)
    permissions = permissions_for_role(normalized_role)
    has_global_scope = role_has_global_game_access(normalized_role)

    allowed_game_ids: set[int] = set()
    allowed_game_slugs: set[str] = set()

    if not has_global_scope:
        rows = (
            db.query(StaffGameAccess.game_id, Game.slug)
            .join(Game, Game.id == StaffGameAccess.game_id)
            .filter(StaffGameAccess.admin_user_id == user.id)
            .all()
        )
        allowed_game_ids = {int(game_id) for game_id, _slug in rows}
        allowed_game_slugs = {slug for _game_id, slug in rows if slug}

    return StaffPrincipal(
        user_id=user.id,
        username=user.username,
        role=normalized_role,
        permissions=permissions,
        has_global_game_access=has_global_scope,
        allowed_game_ids=frozenset(allowed_game_ids),
        allowed_game_slugs=frozenset(allowed_game_slugs),
    )


def build_staff_session_payload(staff: StaffPrincipal) -> dict[str, object]:
    return {
        "username": staff.username,
        "role": staff.role,
        "permissions": staff.permissions.to_dict(),
        "has_global_game_access": staff.has_global_game_access,
        "allowed_game_slugs": sorted(staff.allowed_game_slugs),
    }


def get_current_staff(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> StaffPrincipal:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Staff account not found")

    return build_staff_principal(db, user)


# Backward-compatible alias for existing imports.
def require_admin(staff: StaffPrincipal = Depends(get_current_staff)) -> StaffPrincipal:
    return staff


def require_permission(permission: PermissionName):
    def dependency(staff: StaffPrincipal = Depends(get_current_staff)) -> StaffPrincipal:
        if not staff.can(permission):
            raise HTTPException(status_code=403, detail="Forbidden")
        return staff

    return dependency


require_recruit_viewer = require_permission("can_view_recruits")
require_recruit_manager = require_permission("can_manage_recruits")
require_recruit_deleter = require_permission("can_delete_recruits")
require_announcement_manager = require_permission("can_manage_announcements")
require_announcement_deleter = require_permission("can_delete_announcements")
require_schedule_manager = require_permission("can_manage_schedule")
require_schedule_deleter = require_permission("can_delete_schedule")
require_user_manager = require_permission("can_manage_users")


def ensure_game_access(staff: StaffPrincipal, game_id: int) -> None:
    if staff.has_global_game_access:
        return

    if game_id not in staff.allowed_game_ids:
        raise HTTPException(status_code=403, detail="Forbidden for this game")


def ensure_game_slug_access(db: Session, staff: StaffPrincipal, game_slug: str) -> Game:
    game = db.query(Game).filter(Game.slug == game_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    ensure_game_access(staff, game.id)
    return game


def ensure_recruit_access(db: Session, staff: StaffPrincipal, application_id: int) -> None:
    game_ids = (
        db.query(RecruitGameProfile.game_id)
        .filter(RecruitGameProfile.application_id == application_id)
        .distinct()
        .all()
    )
    if not game_ids and not staff.has_global_game_access:
        raise HTTPException(status_code=403, detail="Forbidden for this recruit")

    for (game_id,) in game_ids:
        ensure_game_access(staff, game_id)


def apply_game_scope_filter(query: Query, game_id_column, staff: StaffPrincipal) -> Query:
    if staff.has_global_game_access:
        return query

    if not staff.allowed_game_ids:
        return query.filter(false())

    return query.filter(game_id_column.in_(tuple(staff.allowed_game_ids)))
