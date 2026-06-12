import math
import numpy as np
from src.database import SessionLocal
from src.models import Team, Match
from src.config import ELO_INITIAL, K_FACTOR, HOME_ADVANTAGE, TOURNAMENT_WEIGHTS, SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
from src.calculate_elo import expected_score, calculate_new_rating

def get_calibrated_draw_prob(rating_a: float, rating_b: float) -> float:
    diff = abs(rating_a - rating_b)
    return 0.28 * math.exp(- (diff / 370.0)**2)

def main():
    db = SessionLocal()
    teams = db.query(Team).all()
    ratings = {team.name: ELO_INITIAL for team in teams}
    
    matches = db.query(Match).order_by(Match.date).all()
    
    # Metrics for Raw Elo (Binary perspective)
    raw_correct = 0
    raw_total_decisive = 0
    raw_log_loss_sum = 0.0
    raw_brier_sum = 0.0
    raw_total_matches = 0
    
    # Metrics for Calibrated Draw (3-way perspective)
    calib_correct = 0
    calib_log_loss_sum = 0.0
    calib_brier_sum = 0.0
    
    for match in matches:
        home = match.home_team
        away = match.away_team

        if home not in ratings or away not in ratings:
            continue
            
        r_home = ratings[home]
        r_away = ratings[away]
        h_adv = 0 if match.neutral else HOME_ADVANTAGE
        
        e_home = expected_score(r_home, r_away, h_adv)
        
        # Actual outcome
        if match.home_score > match.away_score:
            actual = 1.0
            actual_3way = 0 # 0=Home, 1=Draw, 2=Away
            s_home, s_away = 1.0, 0.0
        elif match.home_score < match.away_score:
            actual = 0.0
            actual_3way = 2
            s_home, s_away = 0.0, 1.0
        else:
            actual = 0.5
            actual_3way = 1
            if match.shootout_winner == home:
                s_home, s_away = SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
            elif match.shootout_winner == away:
                s_home, s_away = SHOOTOUT_LOSS_SCORE, SHOOTOUT_WIN_SCORE
            else:
                s_home, s_away = 0.5, 0.5
                
        # 1. Evaluate Raw Elo
        raw_total_matches += 1
        p_raw = max(min(e_home, 0.999), 0.001)
        raw_brier_sum += (p_raw - actual) ** 2
        raw_log_loss_sum -= (actual * math.log(p_raw) + (1 - actual) * math.log(1 - p_raw))
        
        if actual != 0.5:
            raw_total_decisive += 1
            predicted = 1 if e_home > 0.5 else 0
            if predicted == int(actual):
                raw_correct += 1
                
        # 2. Evaluate Calibrated Draw
        p_draw = get_calibrated_draw_prob(r_home + h_adv, r_away)
        p_home = max(0.001, e_home - 0.5 * p_draw)
        p_away = max(0.001, 1 - e_home - 0.5 * p_draw)
        
        # Normalize
        total_p = p_home + p_draw + p_away
        p_home /= total_p
        p_draw /= total_p
        p_away /= total_p
        
        probs = [p_home, p_draw, p_away]
        
        if np.argmax(probs) == actual_3way:
            calib_correct += 1
            
        calib_log_loss_sum -= math.log(probs[actual_3way])
        
        # 3-way Brier score
        for i in range(3):
            y_i = 1.0 if i == actual_3way else 0.0
            calib_brier_sum += (probs[i] - y_i) ** 2
            
        # Update ratings
        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)
        e_away = expected_score(r_away, r_home, -h_adv)
        ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)
        
    print(f"Total Matches Evaluated: {raw_total_matches}")
    print("\n=== 1. Raw Elo (Binary Evaluation) ===")
    print(f"Accuracy (Decisive Matches Only): {raw_correct / raw_total_decisive * 100:.2f}%")
    print(f"Log Loss (Binary formulation): {raw_log_loss_sum / raw_total_matches:.4f}")
    print(f"Brier Score (Binary formulation): {raw_brier_sum / raw_total_matches:.4f}")
    
    print("\n=== 2. Elo + Calibrated Draw (3-Way Evaluation) ===")
    print(f"Accuracy (All Matches, 3-way): {calib_correct / raw_total_matches * 100:.2f}%")
    print(f"Log Loss (Categorical Cross-Entropy): {calib_log_loss_sum / raw_total_matches:.4f}")
    print(f"Brier Score (3-way, scaled by 0.5 for parity): {(calib_brier_sum / 2) / raw_total_matches:.4f}")

    db.close()

if __name__ == "__main__":
    main()
