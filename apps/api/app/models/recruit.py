from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class RecruitApplication(Base):
    __tablename__ = "recruit_applications"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    discord = Column(String, nullable=False)
    current_school = Column(String)
    city_state = Column(String)
    graduation_year = Column(Integer)
    preferred_contact = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    availability = relationship("RecruitAvailability", back_populates="application", uselist=False)
    profiles = relationship("RecruitGameProfile", back_populates="application")

class RecruitAvailability(Base):
    __tablename__ = "recruit_availability"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("recruit_applications.id"))
    hours_per_week = Column(Integer)
    weeknights_available = Column(Boolean, default=False)
    weekends_available = Column(Boolean, default=False)

    application = relationship("RecruitApplication", back_populates="availability")

class RecruitGameProfile(Base):
    #Valorant-specific for now, but could be extended to other games in the future
    __tablename__ = "recruit_game_profiles"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("recruit_applications.id"))
    game_id = Column(Integer, ForeignKey("games.id"))

    ign = Column(String)
    current_rank_label = Column(String)
    current_rank_numeric = Column(Float)
    peak_rank_label = Column(String)
    peak_rank_numeric = Column(Float)

    primary_role = Column(String)
    secondary_role = Column(String)

    tracker_url = Column(String)
    team_experience = Column(Boolean, default=False)
    scrim_experience = Column(Boolean, default=False)
    tournament_experience = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("RecruitApplication", back_populates="profiles")

class RecruitRanking(Base):
    __tablename__ = "recruit_rankings"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("recruit_applications.id"))
    game_id = Column(Integer)
    score = Column(Float)
    explanation_json = Column(JSON)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

