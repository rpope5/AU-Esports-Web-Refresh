from app.services.scoring.valorant import score_valorant
from app.services.scoring.cs2 import score_cs2
from app.services.scoring.fortnite import score_fortnite
from app.services.scoring.r6 import score_r6
from app.services.scoring.rocket_league import score_rocket_league
from app.services.scoring.overwatch import score_overwatch
from app.services.scoring.cod import score_cod
from app.services.scoring.hearthstone import score_hearthstone
from app.services.scoring.smash import score_smash


SCORERS = {
    "valorant": score_valorant,
    "cs2": score_cs2,
    "fortnite": score_fortnite,
    "r6": score_r6,
    "rocket-league": score_rocket_league,
    "overwatch": score_overwatch,
    "cod": score_cod,
    "hearthstone": score_hearthstone,
    "smash":score_smash,
}