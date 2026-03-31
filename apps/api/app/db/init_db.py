# Import all models here so Base knows about them
from app.db.base import Base  # noqa: F401

from app.models.game import Game  # noqa: F401
from app.models.recruit import (  # noqa: F401
    RecruitApplication,
    RecruitAvailability,
    RecruitGameProfile,
    RecruitRanking,
)
from app.models import roster

# If you add AdminUser later, import it here too.
# from app.models.user import AdminUser  # noqa: F401
