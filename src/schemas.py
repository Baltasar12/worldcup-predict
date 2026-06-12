from pydantic import BaseModel
from typing import List, Dict

class RankingResponse(BaseModel):
    rank: int
    team: str
    elo: float

class TeamResponse(BaseModel):
    team: str
    elo: float

class PredictionResponse(BaseModel):
    team_a: str
    team_b: str
    elo_a: float
    elo_b: float
    win_probability_a: float
    draw_probability: float
    win_probability_b: float
    favorite: str

class SimulationRequest(BaseModel):
    teams: List[str]

class ChampionProb(BaseModel):
    team: str
    probability: float

class SimulationResponse(BaseModel):
    simulations_run: int
    champions: List[ChampionProb]
