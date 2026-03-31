# Import all models so Alembic can detect them

from .admin_user import AdminUser
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
    "Game",
    "RecruitApplication",
    "RecruitAvailability",
    "RecruitGameProfile",
    "RecruitRanking",
    "RecruitReview",
    "Player",
]