from app.db.session import SessionLocal
from app.models.game import Game

db = SessionLocal()

games = db.query(Game).all()

for g in games:
    print(g.id, g.name, g.slug)

db.close()