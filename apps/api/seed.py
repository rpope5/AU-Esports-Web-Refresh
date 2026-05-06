from app.db.session import SessionLocal
from app.models.game import Game
from app.models.staff_profile import StaffProfile

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


PJ_FISCUS_SEED = {
    "slug": "pj-fiscus",
    "full_name": "P.J. Fiscus",
    "title": "Head esports Coach",
    "category": "coach",
    "email": "pjfiscus@ashland.edu",
    "game_scope": ["Counter-Strike 2", "Call of Duty", "All Teams"],
    "year_label": "Second in 2025-26",
    "previous_college": "Shawnee State '24",
    "bio_at_ashland": [
        "Fiscus is in his second season as the Eagles' head esports coach.",
        "In Year 1, he guided AU to a top-eight national ending in the fall and a top-16 finish in the spring in Counter-Strike 2, as well as a top-16 showing in NACE for the Call of Duty team.",
    ],
    "bio_before_ashland": [
        "Has been an esports employee at The Vault Ohio since 2024.",
        "Served as esports intern at his alma mater, Shawnee State, in 2023-24.",
        "Was esports assistant coach at Lynchburg-Clay High School from 2022-24.",
    ],
    "sort_order": 0,
    "is_active": True,
}


def seed_staff_profiles():
    db = SessionLocal()
    try:
        existing = db.query(StaffProfile).filter(StaffProfile.slug == PJ_FISCUS_SEED["slug"]).first()
        if existing:
            print("P.J. Fiscus staff profile already seeded.")
            return

        db.add(StaffProfile(**PJ_FISCUS_SEED))
        db.commit()
        print("Seeded P.J. Fiscus staff profile.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_games()
    seed_staff_profiles()
