from app.db.session import SessionLocal
from app.models.game import Game

GAMES_TO_SEED = [
    {"name": "Valorant", "slug": "valorant"},
    {"name": "Counter-Strike 2", "slug": "cs2"},
    {"name": "Fortnite", "slug": "fortnite"},
    {"name": "Hearthstone", "slug": "hearthstone"},
    {"name": "Call of Duty", "slug": "cod"},
    {"name": "Tom Clancy's Rainbow Six Siege", "slug": "r6"},
    {"name": "Rocket League", "slug": "rocket-league"},
    {"name": "Overwatch", "slug": "overwatch"},
    {"name": "Super Smash Bros. Ultimate", "slug": "smash"},
    {"name": "Mario Kart", "slug": "mario-kart"},
]

def seed_games():
    db = SessionLocal()

    for game_data in GAMES_TO_SEED:
        existing = db.query(Game).filter(Game.slug == game_data["slug"]).first()
        if existing:
            print(f'{game_data["name"]} already seeded.')
            continue

        game = Game(
            name=game_data["name"],
            slug=game_data["slug"]
        )
        db.add(game)
        print(f'Seeded {game_data["name"]}.')

    db.commit()
    db.close()
    print("Done seeding games.")

if __name__ == "__main__":
    seed_games()