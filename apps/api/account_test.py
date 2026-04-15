from app.db.session import SessionLocal
from app.core.passwords import hash_password
from app.models.admin_user import AdminUser
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess

ACCOUNTS = [
    ("rpope_coach",   "One4cigs2370!",   "coach",    ["mario-kart", "smash"]),
    
]

db = SessionLocal()
try:
    slug_to_id = {g.slug: g.id for g in db.query(Game).all()}
    for required in ("valorant", "smash"):
        if required not in slug_to_id:
            raise RuntimeError(f"Missing game slug: {required}. Run seed.py first.")

    for username, password, role, scope_slugs in ACCOUNTS:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if user is None:
            user = AdminUser(
                username=username,
                email=None,
                role=role,
                password_hash=hash_password(password),
            )
            db.add(user)
            db.flush()
            action = "created"
        else:
            user.role = role
            user.password_hash = hash_password(password)  # reset to known test password
            action = "updated"

        db.query(StaffGameAccess).filter(
            StaffGameAccess.admin_user_id == user.id
        ).delete(synchronize_session=False)

        for slug in scope_slugs:
            db.add(StaffGameAccess(admin_user_id=user.id, game_id=slug_to_id[slug]))

        scope_label = scope_slugs if scope_slugs else ["<none/global override>"]
        print(f"{action}: {username} role={role} scopes={scope_label}")

    db.commit()
finally:
    db.close()

