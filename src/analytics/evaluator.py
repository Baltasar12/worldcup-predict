import os
import json
import numpy as np
from src.database import SessionLocal
from src.models import Team, Match
from src.config import ELO_INITIAL, K_FACTOR, HOME_ADVANTAGE, TOURNAMENT_WEIGHTS, SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
from src.calculate_elo import expected_score, calculate_new_rating
from src.evaluate_models import get_calibrated_draw_prob
from .metrics import calculate_accuracy, calculate_log_loss, calculate_brier_score
from .calibration import compute_calibration_bins

def run_evaluation():
    db = SessionLocal()
    teams = db.query(Team).all()
    ratings = {team.name: ELO_INITIAL for team in teams}
    matches = db.query(Match).order_by(Match.date).all()
    
    total_matches = 0
    correct = 0
    log_loss_sum = 0.0
    brier_sum = 0.0
    
    predictions = []
    actuals = []
    
    world_cup_tournaments = {"2014": {}, "2018": {}, "2022": {}}
    
    for match in matches:
        home = match.home_team
        away = match.away_team
        
        if home not in ratings or away not in ratings:
            continue
            
        r_home = ratings[home]
        r_away = ratings[away]
        h_adv = 0 if match.neutral else HOME_ADVANTAGE
        
        e_home = expected_score(r_home, r_away, h_adv)
        p_draw = get_calibrated_draw_prob(r_home + h_adv, r_away)
        p_home = max(0.001, e_home - 0.5 * p_draw)
        p_away = max(0.001, 1 - e_home - 0.5 * p_draw)
        
        total_p = p_home + p_draw + p_away
        probs = [p_home / total_p, p_draw / total_p, p_away / total_p]
        
        if match.home_score > match.away_score:
            actual = 0
            s_home, s_away = 1.0, 0.0
        elif match.home_score < match.away_score:
            actual = 2
            s_home, s_away = 0.0, 1.0
        else:
            actual = 1
            if match.shootout_winner == home:
                s_home, s_away = SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
            elif match.shootout_winner == away:
                s_home, s_away = SHOOTOUT_LOSS_SCORE, SHOOTOUT_WIN_SCORE
            else:
                s_home, s_away = 0.5, 0.5
                
        # Metrics
        total_matches += 1
        correct += calculate_accuracy(probs, actual)
        log_loss_sum += calculate_log_loss(probs, actual)
        brier_sum += calculate_brier_score(probs, actual)
        
        predictions.append({"home": probs[0], "draw": probs[1], "away": probs[2]})
        actuals.append(actual)
        
        # World Cup tracking
        if match.tournament == "FIFA World Cup":
            year = str(match.date)[:4]
            if year in world_cup_tournaments:
                if "elo_snapshot" not in world_cup_tournaments[year]:
                    world_cup_tournaments[year]["elo_snapshot"] = ratings.copy()
                world_cup_tournaments[year]["last_match"] = match
                
        # Update Elo
        e_away = expected_score(r_away, r_home, -h_adv)
        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)
        ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)
        
    db.close()
    
    # Process World Cups
    wc_results = []
    for year in ["2014", "2018", "2022"]:
        data = world_cup_tournaments[year]
        if "last_match" in data:
            last = data["last_match"]
            # Champion is the winner of the last match
            if last.home_score > last.away_score or last.shootout_winner == last.home_team:
                champion = last.home_team
            else:
                champion = last.away_team
            
            snap = data["elo_snapshot"]
            ranked_teams = sorted(snap.items(), key=lambda x: x[1], reverse=True)
            top_teams = [t[0] for t in ranked_teams[:5]]
            
            champ_rank = next((i+1 for i, t in enumerate(ranked_teams) if t[0] == champion), -1)
            
            wc_results.append({
                "year": int(year),
                "champion": champion,
                "champion_predicted_rank": champ_rank,
                "top_predicted_teams": top_teams
            })

    summary = {
        "accuracy": correct / total_matches if total_matches > 0 else 0,
        "log_loss": log_loss_sum / total_matches if total_matches > 0 else 0,
        "brier_score": brier_sum / total_matches if total_matches > 0 else 0,
        "evaluated_matches": total_matches,
        "world_cups": wc_results
    }
    
    calibration = compute_calibration_bins(predictions, actuals)
    
    return summary, calibration
