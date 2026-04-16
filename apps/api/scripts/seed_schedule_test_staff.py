from app.core.passwords import hash_password
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess

TEST_PASSWORD = ""
TEST_ACCOUNTS = [
    
]


def seed_schedule_test_staff() -> None:
    db = SessionLocal()
    try:
        slug_to_id = {game.slug: game.id for game in db.query(Game).all()}

        for username, role, scope_slugs in TEST_ACCOUNTS:
            missing_slugs = [slug for slug in scope_slugs if slug not in slug_to_id]
            if missing_slugs:
                missing = ", ".join(sorted(missing_slugs))
                raise RuntimeError(
                    f"Missing game slug(s): {missing}. Run `python seed.py` first."
                )

            user = db.query(AdminUser).filter(AdminUser.username == username).first()
            if user is None:
                user = AdminUser(
                    username=username,
                    email=None,
                    role=role,
                    password_hash=hash_password(TEST_PASSWORD),
                )
                db.add(user)
                db.flush()
                action = "created"
            else:
                user.role = role
                user.password_hash = hash_password(TEST_PASSWORD)
                action = "updated"

            db.query(StaffGameAccess).filter(
                StaffGameAccess.admin_user_id == user.id
            ).delete(synchronize_session=False)

            for slug in scope_slugs:
                db.add(
                    StaffGameAccess(
                        admin_user_id=user.id,
                        game_id=slug_to_id[slug],
                    )
                )

            scope_label = scope_slugs if scope_slugs else ["<global>"]
            print(f"{action}: {username} role={role} scopes={scope_label}")

        db.commit()
        print(f"Done. Seeded schedule workflow test accounts with password: {TEST_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_schedule_test_staff()
