from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import StaffPrincipal, get_db, require_user_manager
from app.core.passwords import hash_password
from app.core.roles import StaffRole, normalize_staff_role, role_has_global_game_access
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess
from app.schemas.users import (
    ManagedUserCreate,
    ManagedUserOut,
    ManagedUserUpdate,
    PasswordResetRequest,
    UserManagementOptionsOut,
    UserScopeOut,
)

router = APIRouter()

MANAGEABLE_ROLES_BY_ACTOR: dict[StaffRole, set[StaffRole]] = {
    "admin": {"admin", "head_coach", "coach", "captain"},
    "head_coach": {"coach", "captain"},
    "coach": set(),
    "captain": set(),
}


def _actor_scope_ids_for_user_management(actor: StaffPrincipal) -> set[int]:
    if actor.has_global_game_access:
        return set()

    return {int(game_id) for game_id in actor.allowed_game_ids}


def _scope_rows_for_users(db: Session, user_ids: list[int]) -> dict[int, list[UserScopeOut]]:
    scope_map: dict[int, list[UserScopeOut]] = defaultdict(list)
    if not user_ids:
        return scope_map

    rows = (
        db.query(
            StaffGameAccess.admin_user_id,
            Game.id,
            Game.slug,
            Game.name,
        )
        .join(Game, Game.id == StaffGameAccess.game_id)
        .filter(StaffGameAccess.admin_user_id.in_(user_ids))
        .order_by(Game.name.asc(), Game.slug.asc())
        .all()
    )
    for admin_user_id, game_id, slug, name in rows:
        scope_map[int(admin_user_id)].append(
            UserScopeOut(
                game_id=int(game_id),
                game_slug=slug,
                game_name=name,
            )
        )
    return scope_map


def _scope_ids_for_user(db: Session, user_id: int) -> set[int]:
    rows = (
        db.query(StaffGameAccess.game_id)
        .filter(StaffGameAccess.admin_user_id == user_id)
        .all()
    )
    return {int(game_id) for (game_id,) in rows}


def _can_manage_target(
    actor: StaffPrincipal,
    target_role: StaffRole,
    target_scope_ids: set[int],
    actor_scope_ids: set[int],
) -> bool:
    if actor.role == "admin":
        return True

    if actor.role == "head_coach":
        if target_role not in {"coach", "captain"}:
            return False
        if actor.has_global_game_access:
            return True
        return target_scope_ids.issubset(actor_scope_ids)

    return False


def _assignable_roles_for_actor(actor: StaffPrincipal) -> list[StaffRole]:
    allowed = MANAGEABLE_ROLES_BY_ACTOR.get(actor.role, set())
    ordered: list[StaffRole] = ["admin", "head_coach", "coach", "captain"]
    return [role for role in ordered if role in allowed]


def _ensure_role_assignable(actor: StaffPrincipal, role: StaffRole) -> None:
    if role not in MANAGEABLE_ROLES_BY_ACTOR.get(actor.role, set()):
        raise HTTPException(status_code=403, detail="Forbidden role assignment")


def _validate_game_ids(db: Session, game_ids: set[int]) -> list[Game]:
    if not game_ids:
        return []

    games = db.query(Game).filter(Game.id.in_(tuple(game_ids))).all()
    found_ids = {game.id for game in games}
    missing = sorted(game_id for game_id in game_ids if game_id not in found_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"Invalid game IDs: {missing}")
    return games


def _apply_scope_assignments(db: Session, user_id: int, game_ids: set[int]) -> None:
    (
        db.query(StaffGameAccess)
        .filter(StaffGameAccess.admin_user_id == user_id)
        .delete(synchronize_session=False)
    )
    for game_id in sorted(game_ids):
        db.add(StaffGameAccess(admin_user_id=user_id, game_id=game_id))


def _active_admin_count(db: Session) -> int:
    admins = db.query(AdminUser.role, AdminUser.is_active).all()
    return sum(
        1
        for role, is_active in admins
        if bool(is_active) and normalize_staff_role(role) == "admin"
    )


def _serialize_user(
    actor: StaffPrincipal,
    user: AdminUser,
    scope_map: dict[int, list[UserScopeOut]],
    actor_scope_ids: set[int],
) -> ManagedUserOut:
    normalized_role = normalize_staff_role(user.role)
    scopes = scope_map.get(user.id, [])
    scope_ids = {scope.game_id for scope in scopes}
    manageable = _can_manage_target(actor, normalized_role, scope_ids, actor_scope_ids)

    return ManagedUserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=normalized_role,
        is_active=bool(user.is_active),
        must_change_password=bool(user.must_change_password),
        has_global_game_access=role_has_global_game_access(normalized_role),
        scopes=scopes,
        created_at=user.created_at,
        updated_at=user.updated_at,
        manageable=manageable,
    )


@router.get("/admin/users/options", response_model=UserManagementOptionsOut)
def get_user_management_options(
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    assignable_roles = _assignable_roles_for_actor(actor)
    actor_scope_ids = _actor_scope_ids_for_user_management(actor)

    all_games = db.query(Game).order_by(Game.name.asc(), Game.slug.asc()).all()
    all_game_payload = [
        UserScopeOut(game_id=game.id, game_slug=game.slug, game_name=game.name)
        for game in all_games
    ]

    if actor.role == "admin" or actor.has_global_game_access:
        scope_games = all_game_payload
        scope_ids = [game.id for game in all_games]
        scope_slugs = [game.slug for game in all_games]
    else:
        scope_games = [game for game in all_game_payload if game.game_id in actor_scope_ids]
        scope_ids = [game.game_id for game in scope_games]
        scope_slugs = [game.game_slug for game in scope_games]

    return UserManagementOptionsOut(
        viewer_role=actor.role,
        assignable_roles=assignable_roles,
        scope_game_ids=scope_ids,
        scope_game_slugs=scope_slugs,
        games=scope_games,
    )


@router.get("/admin/users", response_model=list[ManagedUserOut])
def list_users(
    search: str | None = Query(default=None),
    role: StaffRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    game_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    query = db.query(AdminUser)
    if search:
        clean_search = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AdminUser.username.ilike(clean_search),
                AdminUser.email.ilike(clean_search),
            )
        )
    if role:
        query = query.filter(AdminUser.role == role)
    if is_active is not None:
        query = query.filter(AdminUser.is_active.is_(is_active))

    users = query.order_by(AdminUser.username.asc(), AdminUser.id.asc()).limit(limit).all()
    scope_map = _scope_rows_for_users(db, [user.id for user in users])
    actor_scope_ids = _actor_scope_ids_for_user_management(actor)

    serialized = []
    for user in users:
        item = _serialize_user(actor, user, scope_map, actor_scope_ids)
        if game_id is not None and game_id not in {scope.game_id for scope in item.scopes}:
            continue
        if actor.role == "head_coach" and not item.manageable:
            continue
        serialized.append(item)

    return serialized


@router.get("/admin/users/{user_id}", response_model=ManagedUserOut)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    actor_scope_ids = _actor_scope_ids_for_user_management(actor)
    scope_map = _scope_rows_for_users(db, [user.id])
    item = _serialize_user(actor, user, scope_map, actor_scope_ids)
    if actor.role == "head_coach" and not item.manageable:
        raise HTTPException(status_code=403, detail="Forbidden")
    return item


@router.post("/admin/users", response_model=ManagedUserOut, status_code=201)
def create_user(
    data: ManagedUserCreate,
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    _ensure_role_assignable(actor, data.role)

    actor_scope_ids = _actor_scope_ids_for_user_management(actor)
    target_scope_ids = set(data.game_ids)
    _validate_game_ids(db, target_scope_ids)

    if (
        actor.role == "head_coach"
        and not actor.has_global_game_access
        and not target_scope_ids.issubset(actor_scope_ids)
    ):
        raise HTTPException(status_code=403, detail="Cannot assign scopes outside your own scope")

    existing_username = db.query(AdminUser.id).filter(AdminUser.username == data.username).first()
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already exists")

    if data.email:
        existing_email = db.query(AdminUser.id).filter(AdminUser.email == data.email).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already exists")

    user = AdminUser(
        username=data.username,
        email=data.email,
        role=data.role,
        password_hash=hash_password(data.password),
        is_active=bool(data.is_active),
        must_change_password=bool(data.must_change_password),
    )
    db.add(user)
    db.flush()

    _apply_scope_assignments(db, user.id, target_scope_ids)

    db.commit()
    db.refresh(user)

    scope_map = _scope_rows_for_users(db, [user.id])
    return _serialize_user(actor, user, scope_map, actor_scope_ids)


@router.patch("/admin/users/{user_id}", response_model=ManagedUserOut)
def update_user(
    user_id: int,
    data: ManagedUserUpdate,
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    actor_scope_ids = _actor_scope_ids_for_user_management(actor)

    current_role = normalize_staff_role(user.role)
    current_scope_ids = _scope_ids_for_user(db, user.id)
    if actor.role == "head_coach" and not _can_manage_target(
        actor,
        current_role,
        current_scope_ids,
        actor_scope_ids,
    ):
        raise HTTPException(status_code=403, detail="Forbidden")

    next_role = current_role
    if "role" in update_data:
        requested_role = update_data["role"]
        if requested_role is None:
            raise HTTPException(status_code=400, detail="role cannot be null")
        _ensure_role_assignable(actor, requested_role)
        next_role = requested_role

    next_scope_ids = current_scope_ids
    if "game_ids" in update_data:
        requested_game_ids = update_data["game_ids"] or []
        next_scope_ids = set(requested_game_ids)
        _validate_game_ids(db, next_scope_ids)

    if actor.role == "head_coach":
        if not actor.has_global_game_access and not next_scope_ids.issubset(actor_scope_ids):
            raise HTTPException(status_code=403, detail="Cannot assign scopes outside your own scope")
        if not _can_manage_target(actor, next_role, next_scope_ids, actor_scope_ids):
            raise HTTPException(status_code=403, detail="Forbidden")

    next_is_active = bool(update_data.get("is_active", user.is_active))

    if current_role == "admin" and bool(user.is_active):
        losing_active_admin = next_role != "admin" or not next_is_active
        if losing_active_admin and _active_admin_count(db) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last active admin")

    if "email" in update_data:
        next_email = update_data["email"]
        if next_email and next_email != user.email:
            email_owner = db.query(AdminUser.id).filter(AdminUser.email == next_email).first()
            if email_owner and email_owner[0] != user.id:
                raise HTTPException(status_code=409, detail="Email already exists")
        user.email = next_email

    if "role" in update_data:
        user.role = next_role
    if "is_active" in update_data:
        user.is_active = next_is_active
    if "must_change_password" in update_data:
        user.must_change_password = bool(update_data["must_change_password"])
    if "game_ids" in update_data:
        _apply_scope_assignments(db, user.id, next_scope_ids)

    db.commit()
    db.refresh(user)

    scope_map = _scope_rows_for_users(db, [user.id])
    return _serialize_user(actor, user, scope_map, actor_scope_ids)


@router.post("/admin/users/{user_id}/reset-password", response_model=ManagedUserOut)
def reset_user_password(
    user_id: int,
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
    actor: StaffPrincipal = Depends(require_user_manager),
):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    actor_scope_ids = _actor_scope_ids_for_user_management(actor)
    target_role = normalize_staff_role(user.role)
    target_scope_ids = _scope_ids_for_user(db, user.id)
    if not _can_manage_target(actor, target_role, target_scope_ids, actor_scope_ids):
        raise HTTPException(status_code=403, detail="Forbidden")

    user.password_hash = hash_password(data.new_password)
    user.must_change_password = bool(data.must_change_password)
    db.commit()
    db.refresh(user)

    scope_map = _scope_rows_for_users(db, [user.id])
    return _serialize_user(actor, user, scope_map, actor_scope_ids)
