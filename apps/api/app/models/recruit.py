from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

RECRUIT_REVIEW_STATUSES = (
    "NEW",
    "REVIEWED",
    "CONTACTED",
    "TRYOUT",
    "WATCHLIST",
    "ACCEPTED",
    "REJECTED",
)

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
    __tablename__ = "recruit_game_profiles"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("recruit_applications.id"))
    game_id = Column(Integer, ForeignKey("games.id"))

    ign = Column(String)
    fortnite_mode = Column(String, nullable=True)
    ranked_wins = Column(Integer, nullable=True)
    years_played = Column(Integer, nullable=True)
    legend_peak_rank = Column(Integer, nullable=True)
    preferred_format = Column(String, nullable=True)
    other_card_games = Column(String, nullable=True)
    gsp = Column(Integer, nullable=True)
    regional_rank = Column(String, nullable=True)
    best_wins = Column(String, nullable=True)
    characters = Column(String, nullable=True)
    lounge_rating = Column(Integer, nullable=True)
    preferred_title = Column(String, nullable=True)
    controller_type = Column(String, nullable=True)
    playstyle = Column(String, nullable=True)
    preferred_tracks = Column(String, nullable=True)
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
    game_id = Column(Integer, ForeignKey("games.id"))
    score = Column(Float)
    explanation_json = Column(JSON)
    model_version = Column(String)
    raw_inputs_json = Column(JSON, nullable=False, default=dict)
    normalized_features_json = Column(JSON, nullable=False, default=dict)
    scoring_method = Column(String, nullable=False, default="rules")
    is_current = Column(Boolean, nullable=False, default=True)
    scored_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class RecruitReview(Base):
    __tablename__ = "recruit_reviews"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("recruit_applications.id"))
    status = Column(String, nullable=False, default="NEW")
    reviewer_user_id = Column(Integer, nullable=True)
    labeled_at = Column(DateTime, nullable=True)
    label_reason = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

