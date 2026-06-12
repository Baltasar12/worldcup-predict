from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import math
import random
from collections import defaultdict
from typing import List

from src.database import SessionLocal
from src.models import Team, TeamRating
from src.calculate_elo import expected_score
from src.schemas import (
    RankingResponse, TeamResponse, PredictionResponse, 
    SimulationRequest, SimulationResponse, ChampionProb
)

app = FastAPI(
    title="World Cup Prediction Engine",
    description="Probabilistic prediction engine based on historical data and Elo ratings.",
    version="1.0"
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

def get_calibrated_draw_prob(rating_a: float, rating_b: float) -> float:
    diff = abs(rating_a - rating_b)
    # P(Draw) = 0.2800 * exp(-(diff / 370.0000)^2)
    return 0.28 * math.exp(- (diff / 370.0)**2)

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
    team = db.query(Team).filter(Team.name.ilike(team_name)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    rating = db.query(TeamRating).filter(TeamRating.team_id == team.id).first()
    elo_value = rating.rating if rating else 1500.0
    
    return TeamResponse(team=team.name, elo=round(elo_value, 1))

@app.get("/predict", response_model=PredictionResponse)
def predict_match(team_a: str, team_b: str, db: Session = Depends(get_db)):
    t_a = db.query(Team).filter(Team.name.ilike(team_a)).first()
    t_b = db.query(Team).filter(Team.name.ilike(team_b)).first()
    
    if not t_a or not t_b:
        raise HTTPException(status_code=404, detail="One or both teams not found")
        
    r_a_obj = db.query(TeamRating).filter(TeamRating.team_id == t_a.id).first()
    r_b_obj = db.query(TeamRating).filter(TeamRating.team_id == t_b.id).first()
    
    elo_a = r_a_obj.rating if r_a_obj else 1500.0
    elo_b = r_b_obj.rating if r_b_obj else 1500.0
    
    # Calculate Elo Expected Score (which encapsulates Win + 0.5 * Draw)
    exp_a = expected_score(elo_a, elo_b, 0)
    exp_b = expected_score(elo_b, elo_a, 0)
    
    draw_prob = get_calibrated_draw_prob(elo_a, elo_b)
    
    # P(Win) = Expected - 0.5 * P(Draw)
    win_a = exp_a - 0.5 * draw_prob
    win_b = exp_b - 0.5 * draw_prob
    
    # Ensure no negative probabilities due to heuristic edge cases
    win_a = max(0.0, win_a)
    win_b = max(0.0, win_b)
    
    # Normalize back to 1.0 just in case
    total = win_a + win_b + draw_prob
    win_a /= total
    win_b /= total
    draw_prob /= total
    
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
    if len(request.teams) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 teams to simulate")
        
    teams = db.query(Team).filter(Team.name.in_(request.teams)).all()
    found_names = {t.name for t in teams}
    missing = set(request.teams) - found_names
    
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
