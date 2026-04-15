from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

StaffRole = Literal["captain", "coach", "head_coach", "admin"]
PermissionName = Literal[
    "can_view_recruits",
    "can_manage_recruits",
    "can_delete_recruits",
    "can_manage_announcements",
    "can_delete_announcements",
    "can_manage_users",
]

VALID_STAFF_ROLES: tuple[StaffRole, ...] = ("captain", "coach", "head_coach", "admin")
GLOBAL_GAME_ACCESS_ROLES: set[StaffRole] = {"head_coach", "admin"}


@dataclass(frozen=True)
class StaffPermissions:
    can_view_recruits: bool
    can_manage_recruits: bool
    can_delete_recruits: bool
    can_manage_announcements: bool
    can_delete_announcements: bool
    can_manage_users: bool

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


PERMISSIONS_BY_ROLE: dict[StaffRole, StaffPermissions] = {
    "captain": StaffPermissions(
        can_view_recruits=True,
        can_manage_recruits=False,
        can_delete_recruits=False,
        can_manage_announcements=True,
        can_delete_announcements=False,
        can_manage_users=False,
    ),
    "coach": StaffPermissions(
        can_view_recruits=True,
        can_manage_recruits=True,
        can_delete_recruits=False,
        can_manage_announcements=True,
        can_delete_announcements=False,
        can_manage_users=False,
    ),
    "head_coach": StaffPermissions(
        can_view_recruits=True,
        can_manage_recruits=True,
        can_delete_recruits=True,
        can_manage_announcements=True,
        can_delete_announcements=True,
        can_manage_users=False,
    ),
    "admin": StaffPermissions(
        can_view_recruits=True,
        can_manage_recruits=True,
        can_delete_recruits=True,
        can_manage_announcements=True,
        can_delete_announcements=True,
        can_manage_users=True,
    ),
}


def normalize_staff_role(raw_role: str | None) -> StaffRole:
    if raw_role is None:
        return "coach"

    normalized = raw_role.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized == "headcoach":
        normalized = "head_coach"
    if normalized == "administrator":
        normalized = "admin"

    if normalized in VALID_STAFF_ROLES:
        return normalized  # type: ignore[return-value]

    # Legacy values from existing auth flow.
    if normalized == "admin":
        return "admin"
    if normalized == "coach":
        return "coach"

    return "coach"


def permissions_for_role(role: StaffRole) -> StaffPermissions:
    return PERMISSIONS_BY_ROLE[role]


def role_has_global_game_access(role: StaffRole) -> bool:
    return role in GLOBAL_GAME_ACCESS_ROLES
