from app.db.session import engine
from app.db.init_db import Base  # imports models

def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    main()
