# Import all models so Alembic can detect them

from .admin_user import AdminUser
from .announcement import EsportsAnnouncement
from .calendar_event import CalendarEvent
from .game import Game
from .legacy_roster import LegacyRoster, LegacyRosterPlayer, LegacyRosterPlayerGameProfile
from .recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
    RecruitReview,
)
from .roster import Player, PlayerGameProfile
from .staff_game_access import StaffGameAccess

# Optional but nice: define __all__
__all__ = [
    "AdminUser",
    "EsportsAnnouncement",
    "CalendarEvent",
    "Game",
    "LegacyRoster",
    "LegacyRosterPlayer",
    "LegacyRosterPlayerGameProfile",
    "RecruitApplication",
    "RecruitAvailability",
    "RecruitGameProfile",
    "RecruitRanking",
    "RecruitReview",
    "Player",
    "PlayerGameProfile",
    "StaffGameAccess",
]
