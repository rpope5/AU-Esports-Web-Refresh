from app.services.scoring.valorant import score_valorant
from app.services.scoring.cs2 import score_cs2
from app.services.scoring.fortnite import score_fortnite
from app.services.scoring.r6 import score_r6

SCORERS = {
    "valorant": score_valorant,
    "cs2": score_cs2,
    "fortnite": score_fortnite,
    "r6": score_r6,
}