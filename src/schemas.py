from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional

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


# --- World Cup schemas ---

class WorldCupGroupsResponse(BaseModel):
    tournament: str
    groups: Dict[str, List[str]]

class GroupStageMatchResult(BaseModel):
    team_a: str
    team_b: str
    score_a: int
    score_b: int

class TeamStandingResponse(BaseModel):
    team: str
    points: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    elo: float

class GroupStandingsResponse(BaseModel):
    group: str
    standings: List[TeamStandingResponse]
    matches: List[GroupStageMatchResult]

class GroupStageResponse(BaseModel):
    groups: List[GroupStandingsResponse]

class BracketMatchResponse(BaseModel):
    match_id: int
    round: str
    team_a: str
    team_b: str
    team_a_origin: str
    team_b_origin: str

class BracketResponse(BaseModel):
    round_of_32: List[BracketMatchResponse]
    round_of_16: List[BracketMatchResponse] = []
    quarterfinals: List[BracketMatchResponse] = []
    semifinals: List[BracketMatchResponse] = []
    final: List[BracketMatchResponse] = []
    champion: str = ""
    qualified_teams: int

class WorldCupSimulationResponse(BaseModel):
    groups: List[GroupStandingsResponse]
    bracket: BracketResponse

class WorldCupValidationResponse(BaseModel):
    year: int
    champion: str
    champion_predicted_rank: int
    top_predicted_teams: List[str]

class AnalyticsPerformanceResponse(BaseModel):
    accuracy: float
    log_loss: float
    brier_score: float
    evaluated_matches: int
    world_cups: List[WorldCupValidationResponse]

class CalibrationBinResponse(BaseModel):
    bin: str
    count: int
    predicted_prob: float
    actual_prob: float


class ForecastRequest(BaseModel):
    simulations: int
    seed: Optional[int] = None

class TeamForecast(BaseModel):
    team: str
    qualified_from_groups: float
    round_of_16: float
    quarterfinal: float
    semifinal: float
    final: float
    champion: float

class ForecastResponse(BaseModel):
    simulations: int
    results: List[TeamForecast]

class MonteCarloRequest(BaseModel):
    simulations: int
    seed: Optional[int] = None

class MonteCarloTeamResult(BaseModel):
    team: str
    round_of_32: float = Field(alias="round-of-32")
    round_of_16: float = Field(alias="round-of-16")
    quarterfinalist: float
    semifinalist: float
    finalist: float
    champion: float

    model_config = ConfigDict(populate_by_name=True)

class MonteCarloResponse(BaseModel):
    simulations: int
    results: List[MonteCarloTeamResult]
