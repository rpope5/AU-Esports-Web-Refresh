from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gamertag = Column(String, nullable=False)
    role = Column(String, nullable=True)
    game = Column(String, nullable=False)
    year = Column(String, nullable=True)
    major = Column(String, nullable=True)
    headshot = Column(String, nullable=True)  # URL or filename