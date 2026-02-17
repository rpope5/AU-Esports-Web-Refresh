from app.db.session import SessionLocal
from app.models.game import Game

def seed_games():
    db = SessionLocal()

    existing = db.query(Game).filter(Game.slug == "valorant").first()
    if existing:
        print("Valorant already seeded.")
        return

    valorant = Game(
        name="Valorant",
        slug="valorant"
    )

    db.add(valorant)
    db.commit()
    print("Seeded Valorant.")

if __name__ == "__main__":
    seed_games()
