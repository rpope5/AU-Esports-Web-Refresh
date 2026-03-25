from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.core.passwords import hash_password

def seed():
    db = SessionLocal()

    username = ""   # change if you want
    password = ""  # change immediately after testing

    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        print("Admin user already exists.")
        return

    user = AdminUser(
        username=username,
        email=None,
        role="ADMIN",
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    print("Seeded admin user:", username)

if __name__ == "__main__":
    seed()