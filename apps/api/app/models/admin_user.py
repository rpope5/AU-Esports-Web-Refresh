from sqlalchemy import Column, Integer, String
from app.db.base import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(String, nullable=False, default="COACH")  # COACH or ADMIN
    password_hash = Column(String, nullable=False)