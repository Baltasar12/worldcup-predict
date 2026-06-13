from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import List

from src.database import SessionLocal
from src.models import Team, TeamRating
from src.calculate_elo import expected_score
from src.prediction import get_calibrated_draw_prob, get_match_probabilities
from src.schemas import (
    RankingResponse, TeamResponse, PredictionResponse, 
    SimulationRequest, SimulationResponse, ChampionProb,
    WorldCupGroupsResponse, GroupStageResponse, GroupStandingsResponse,
    GroupStageMatchResult, TeamStandingResponse,
    BracketResponse, BracketMatchResponse,
    WorldCupSimulationResponse, ForecastRequest, ForecastResponse, TeamForecast,
    MonteCarloRequest, MonteCarloResponse, MonteCarloTeamResult
)
from src.world_cup.simulator import load_groups, run_group_stage, run_single_simulation, run_monte_carlo_simulation
from src.world_cup.bracket import generate_bracket


TEAM_ALIASES = {
    "USA": "United States",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Czechia": "Czech Republic",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}


def validate_world_cup_dataset():
    """
    Validate that every team in world_cup_2026.json can be resolved
    to an Elo rating in the database. Fails fast with a clear error
    if any teams are unresolved.
    """
    data = load_groups()
    all_team_names = [
        team for teams in data["groups"].values() for team in teams
    ]

    db = SessionLocal()
    try:
        db_teams = {t.name for t in db.query(Team).all()}
        rated_team_ids = {r.team_id for r in db.query(TeamRating).all()}
        rated_teams = {
            t.name for t in db.query(Team).filter(Team.id.in_(rated_team_ids)).all()
        }

        missing_from_db = [t for t in all_team_names if t not in db_teams]
        missing_elo = [t for t in all_team_names if t in db_teams and t not in rated_teams]

        errors = []
        if missing_from_db:
            errors.append(
                f"Teams not found in database: {missing_from_db}"
            )
        if missing_elo:
            errors.append(
                f"Teams found in database but missing Elo ratings: {missing_elo}"
            )

        if errors:
            msg = (
                "World Cup dataset validation failed.\n"
                + "\n".join(errors)
                + "\nFix data/world_cup_2026.json to use exact team names from the database."
            )
            raise RuntimeError(msg)

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle handler."""
    validate_world_cup_dataset()
    yield


app = FastAPI(
    title="World Cup Prediction Engine",
    description="Probabilistic prediction engine based on historical data and Elo ratings.",
    version="1.0",
    lifespan=lifespan,
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0"}



@app.get("/rankings", response_model=List[RankingResponse])
def get_rankings(limit: int = 20, db: Session = Depends(get_db)):
    ratings = db.query(TeamRating).order_by(TeamRating.rating.desc()).limit(limit).all()
    
    response = []
    for i, r in enumerate(ratings):
        response.append(RankingResponse(
            rank=i + 1,
            team=r.team.name,
            elo=round(r.rating, 1)
        ))
    return response

@app.get("/team/{team_name}", response_model=TeamResponse)
def get_team(team_name: str, db: Session = Depends(get_db)):
    team_name = TEAM_ALIASES.get(team_name, team_name)
    team = db.query(Team).filter(Team.name.ilike(team_name)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    rating = db.query(TeamRating).filter(TeamRating.team_id == team.id).first()
    elo_value = rating.rating if rating else 1500.0
    
    return TeamResponse(team=team.name, elo=round(elo_value, 1))

@app.get("/predict", response_model=PredictionResponse)
def predict_match(team_a: str, team_b: str, db: Session = Depends(get_db)):
    team_a = TEAM_ALIASES.get(team_a, team_a)
    team_b = TEAM_ALIASES.get(team_b, team_b)
    
    t_a = db.query(Team).filter(Team.name.ilike(team_a)).first()
    t_b = db.query(Team).filter(Team.name.ilike(team_b)).first()
    
    if not t_a or not t_b:
        raise HTTPException(status_code=404, detail="One or both teams not found")
        
    r_a_obj = db.query(TeamRating).filter(TeamRating.team_id == t_a.id).first()
    r_b_obj = db.query(TeamRating).filter(TeamRating.team_id == t_b.id).first()
    
    elo_a = r_a_obj.rating if r_a_obj else 1500.0
    elo_b = r_b_obj.rating if r_b_obj else 1500.0
    
    win_a, draw_prob, win_b = get_match_probabilities(elo_a, elo_b)
    
    favorite = t_a.name if win_a > win_b else t_b.name
    
    return PredictionResponse(
        team_a=t_a.name,
        team_b=t_b.name,
        elo_a=round(elo_a, 1),
        elo_b=round(elo_b, 1),
        win_probability_a=round(win_a, 4),
        draw_probability=round(draw_prob, 4),
        win_probability_b=round(win_b, 4),
        favorite=favorite
    )

def simulate_knockout(teams_with_ratings: List[tuple]) -> str:
    current_round = teams_with_ratings[:]
    while len(current_round) > 1:
        next_round = []
        for i in range(0, len(current_round), 2):
            if i + 1 >= len(current_round):
                next_round.append(current_round[i])
            else:
                team_a, rat_a = current_round[i]
                team_b, rat_b = current_round[i+1]
                prob_a = expected_score(rat_a, rat_b, 0)
                if random.random() < prob_a:
                    next_round.append(current_round[i])
                else:
                    next_round.append(current_round[i+1])
        current_round = next_round
    return current_round[0][0]

@app.post("/simulate", response_model=SimulationResponse)
def simulate_tournament(request: SimulationRequest, db: Session = Depends(get_db)):
    normalized_teams = [TEAM_ALIASES.get(t, t) for t in request.teams]
    
    if len(normalized_teams) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 teams to simulate")
        
    teams = db.query(Team).filter(Team.name.in_(normalized_teams)).all()
    found_names = {t.name for t in teams}
    missing = set(normalized_teams) - found_names
    
    if missing:
        raise HTTPException(status_code=404, detail=f"Teams not found: {', '.join(missing)}")
        
    ratings = {r.team_id: r.rating for r in db.query(TeamRating).filter(TeamRating.team_id.in_([t.id for t in teams])).all()}
    
    teams_with_ratings = []
    for team in teams:
        r = ratings.get(team.id, 1500.0)
        teams_with_ratings.append((team.name, r))
        
    simulations = 10000
    champions = defaultdict(int)
    
    for _ in range(simulations):
        bracket = teams_with_ratings[:]
        random.shuffle(bracket)
        winner = simulate_knockout(bracket)
        champions[winner] += 1
        
    sorted_champs = sorted(champions.items(), key=lambda x: x[1], reverse=True)
    
    champ_probs = []
    for team_name, wins in sorted_champs:
        champ_probs.append(ChampionProb(
            team=team_name,
            probability=round(wins / simulations, 4)
        ))
        
    return SimulationResponse(
        simulations_run=simulations,
        champions=champ_probs
    )


# --- World Cup endpoints ---

def _build_elo_lookup(db: Session) -> dict[str, float]:
    """Build a team_name -> elo_rating lookup from the database."""
    ratings = db.query(TeamRating).all()
    team_ids = {r.team_id for r in ratings}
    teams = db.query(Team).filter(Team.id.in_(team_ids)).all()
    id_to_name = {t.id: t.name for t in teams}
    return {id_to_name[r.team_id]: r.rating for r in ratings if r.team_id in id_to_name}


def _group_result_to_response(gr) -> GroupStandingsResponse:
    """Convert a GroupResult dataclass to a Pydantic response."""
    return GroupStandingsResponse(
        group=gr.group_name,
        standings=[
            TeamStandingResponse(
                team=s.team,
                points=s.points,
                wins=s.wins,
                draws=s.draws,
                losses=s.losses,
                goals_for=s.goals_for,
                goals_against=s.goals_against,
                goal_difference=s.goal_difference,
                elo=round(s.elo, 1),
            )
            for s in gr.standings
        ],
        matches=[
            GroupStageMatchResult(
                team_a=m.team_a,
                team_b=m.team_b,
                score_a=m.score_a,
                score_b=m.score_b,
            )
            for m in gr.matches
        ],
    )


def _bracket_to_response(bracket) -> BracketResponse:
    """Convert a Bracket dataclass to a Pydantic response."""
    def map_matches(matches, round_name):
        return [
            BracketMatchResponse(
                match_id=bm.match_id,
                round=round_name,
                team_a=bm.team_a,
                team_b=bm.team_b,
                team_a_origin=bm.team_a_origin,
                team_b_origin=bm.team_b_origin,
            )
            for bm in matches
        ]

    return BracketResponse(
        round_of_32=map_matches(bracket.round_of_32, "Round of 32"),
        round_of_16=map_matches(bracket.round_of_16, "Round of 16"),
        quarterfinals=map_matches(bracket.quarterfinals, "Quarterfinal"),
        semifinals=map_matches(bracket.semifinals, "Semifinal"),
        final=map_matches(bracket.final, "Final"),
        champion=bracket.champion,
        qualified_teams=bracket.qualified_teams,
    )


@app.get("/world-cup/groups", response_model=WorldCupGroupsResponse)
def get_world_cup_groups():
    """Return the configured World Cup 2026 groups."""
    data = load_groups()
    return WorldCupGroupsResponse(
        tournament=data["tournament"],
        groups=data["groups"],
    )


@app.post("/world-cup/group-stage", response_model=GroupStageResponse)
def run_world_cup_group_stage(db: Session = Depends(get_db)):
    """Run a single group-stage simulation for all groups."""
    data = load_groups()
    elo_lookup = _build_elo_lookup(db)
    group_results = run_group_stage(data["groups"], elo_lookup)

    return GroupStageResponse(
        groups=[_group_result_to_response(gr) for gr in group_results],
    )


@app.post("/world-cup/bracket", response_model=BracketResponse)
def generate_world_cup_bracket(db: Session = Depends(get_db)):
    """Run group stage and generate the knockout bracket."""
    data = load_groups()
    elo_lookup = _build_elo_lookup(db)
    group_results = run_group_stage(data["groups"], elo_lookup)
    bracket = generate_bracket(group_results)

    return _bracket_to_response(bracket)


@app.post("/world-cup/simulate", response_model=WorldCupSimulationResponse)
def simulate_world_cup(db: Session = Depends(get_db)):
    """Run the complete Sprint 1 workflow: groups + bracket."""
    data = load_groups()
    elo_lookup = _build_elo_lookup(db)
    result = run_single_simulation(data["groups"], elo_lookup)

    return WorldCupSimulationResponse(
        groups=[_group_result_to_response(gr) for gr in result["group_results"]],
        bracket=_bracket_to_response(result["bracket"]),
    )

@app.post("/world-cup/forecast", response_model=ForecastResponse)
def run_world_cup_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    """Run a full Monte Carlo simulation to forecast the tournament."""
    data = load_groups()
    elo_lookup = _build_elo_lookup(db)
    
    # Run the Monte Carlo simulation
    results = run_monte_carlo_simulation(
        simulations=request.simulations, 
        seed=request.seed, 
        groups=data["groups"], 
        elo_lookup=elo_lookup
    )
    
    team_forecasts = []
    for r in results:
        team_forecasts.append(TeamForecast(
            team=r["team"],
            qualified_from_groups=r["qualified_from_groups"],
            round_of_16=r["round_of_16"],
            quarterfinal=r["quarterfinal"],
            semifinal=r["semifinal"],
            final=r["final"],
            champion=r["champion"]
        ))
        
    return ForecastResponse(
        simulations=request.simulations,
        results=team_forecasts
    )

@app.post("/world-cup/monte-carlo", response_model=MonteCarloResponse)
def run_world_cup_monte_carlo(request: MonteCarloRequest, db: Session = Depends(get_db)):
    """Run Monte Carlo simulation matching Sprint 3 contract."""
    if request.simulations not in [1000, 5000, 10000]:
        raise HTTPException(status_code=400, detail="Simulations must be 1000, 5000, or 10000")
        
    data = load_groups()
    elo_lookup = _build_elo_lookup(db)
    
    results = run_monte_carlo_simulation(
        simulations=request.simulations, 
        seed=request.seed, 
        groups=data["groups"], 
        elo_lookup=elo_lookup
    )
    
    team_results = []
    for r in results:
        team_results.append(MonteCarloTeamResult(
            team=r["team"],
            round_of_32=r["qualified_from_groups"],
            round_of_16=r["round_of_16"],
            quarterfinalist=r["quarterfinal"],
            semifinalist=r["semifinal"],
            finalist=r["final"],
            champion=r["champion"]
        ))
        
    return MonteCarloResponse(
        simulations=request.simulations,
        results=team_results
    )
