from app.services.scoring.valorant import score_valorant
from app.services.scoring.cs2 import score_cs2

SCORERS = {
    "valorant": score_valorant,
    "cs2": score_cs2,
}