from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    ratings = relationship("TeamRating", back_populates="team")

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    home_team = Column(String, nullable=False, index=True)
    away_team = Column(String, nullable=False, index=True)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    tournament = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    neutral = Column(Boolean, nullable=False)
    shootout_winner = Column(String, nullable=True)

class TeamRating(Base):
    __tablename__ = 'team_ratings'

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    calculated_at = Column(Date, nullable=False, index=True)

    team = relationship("Team", back_populates="ratings")
