import math
from src.database import SessionLocal
from src.models import Team, Match
from src.config import ELO_INITIAL, K_FACTOR, HOME_ADVANTAGE, TOURNAMENT_WEIGHTS, SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
from src.calculate_elo import expected_score, calculate_new_rating

def main():
    db = SessionLocal()
    teams = db.query(Team).all()
    ratings = {team.name: ELO_INITIAL for team in teams}
    
    print("Loading matches...")
    matches = db.query(Match).order_by(Match.date).all()
    
    correct = 0
    total = 0
    log_loss_sum = 0.0
    brier_sum = 0.0
    
    for match in matches:
        home = match.home_team
        away = match.away_team

        if home not in ratings or away not in ratings:
            continue
            
        r_home = ratings[home]
        r_away = ratings[away]
        
        h_adv = 0 if match.neutral else HOME_ADVANTAGE
        
        # Predictions (pre-match)
        e_home = expected_score(r_home, r_away, h_adv)
        
        # Determine actual outcomes
        if match.home_score > match.away_score:
            actual = 1.0
            s_home, s_away = 1.0, 0.0
        elif match.home_score < match.away_score:
            actual = 0.0
            s_home, s_away = 0.0, 1.0
        else:
            if match.shootout_winner == home:
                s_home, s_away = SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
                actual = 1.0 # For binary accuracy metrics
            elif match.shootout_winner == away:
                s_home, s_away = SHOOTOUT_LOSS_SCORE, SHOOTOUT_WIN_SCORE
                actual = 0.0
            else:
                s_home, s_away = 0.5, 0.5
                actual = 0.5
                
        # Metrics
        if actual != 0.5:
            total += 1
            predicted = 1 if e_home > 0.5 else 0
            if predicted == int(actual):
                correct += 1
                
            p = max(min(e_home, 0.999), 0.001)
            if actual == 1.0:
                log_loss_sum -= math.log(p)
            else:
                log_loss_sum -= math.log(1 - p)
                
            brier_sum += (p - actual) ** 2
            
        # Update
        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)
        e_away = expected_score(r_away, r_home, -h_adv)
        ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)
        
    print("\n--- Backtest Results (V1.0) ---")
    print(f"Total Decisive Matches: {total}")
    print(f"Accuracy: {correct / total * 100:.2f}%")
    print(f"Log Loss: {log_loss_sum / total:.4f}")
    print(f"Brier Score: {brier_sum / total:.4f}")
    
    db.close()

if __name__ == "__main__":
    main()
