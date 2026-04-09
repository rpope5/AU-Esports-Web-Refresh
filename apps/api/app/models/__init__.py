# Import all models so Alembic can detect them

from .admin_user import AdminUser
from .announcement import EsportsAnnouncement
from .game import Game
from .recruit import (
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
    RecruitReview,
)
from .roster import Player

# Optional but nice: define __all__
__all__ = [
    "AdminUser",
    "EsportsAnnouncement",
    "Game",
    "RecruitApplication",
    "RecruitAvailability",
    "RecruitGameProfile",
    "RecruitRanking",
    "RecruitReview",
    "Player",
]
