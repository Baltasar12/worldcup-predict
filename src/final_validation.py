import math
import numpy as np
from datetime import timedelta
from collections import defaultdict
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
    
    if not matches:
        print("No matches found.")
        return
        
    last_date = matches[-1].date
    start_validation_date = last_date - timedelta(days=2 * 365)
    
    validation_records = []
    
    for match in matches:
        home = match.home_team
        away = match.away_team

        if home not in ratings or away not in ratings:
            continue
            
        r_home = ratings[home]
        r_away = ratings[away]
        h_adv = 0 if match.neutral else HOME_ADVANTAGE
        
        # Predictions
        e_home = expected_score(r_home, r_away, h_adv)
        p_draw = get_calibrated_draw_prob(r_home + h_adv, r_away)
        p_home = max(0.001, e_home - 0.5 * p_draw)
        p_away = max(0.001, 1 - e_home - 0.5 * p_draw)
        
        total_p = p_home + p_draw + p_away
        p_home /= total_p
        p_draw /= total_p
        p_away /= total_p
        
        probs = [p_home, p_draw, p_away]
        
        # Outcomes
        if match.home_score > match.away_score:
            actual_idx = 0
            s_home, s_away = 1.0, 0.0
        elif match.home_score < match.away_score:
            actual_idx = 2
            s_home, s_away = 0.0, 1.0
        else:
            actual_idx = 1
            if match.shootout_winner == home:
                s_home, s_away = SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
            elif match.shootout_winner == away:
                s_home, s_away = SHOOTOUT_LOSS_SCORE, SHOOTOUT_WIN_SCORE
            else:
                s_home, s_away = 0.5, 0.5
                
        # Validate if in last 24 months
        if match.date >= start_validation_date:
            predicted_idx = np.argmax(probs)
            confidence = probs[predicted_idx]
            is_correct = (predicted_idx == actual_idx)
            prob_of_actual = probs[actual_idx]
            
            outcome_str = "Home Win" if actual_idx == 0 else "Draw" if actual_idx == 1 else "Away Win"
            pred_str = "Home Win" if predicted_idx == 0 else "Draw" if predicted_idx == 1 else "Away Win"
            
            desc = f"{match.date} | {home} {match.home_score}-{match.away_score} {away}"
            if actual_idx == 1 and match.shootout_winner:
                desc += f" ({match.shootout_winner} won pens)"
                
            validation_records.append({
                'desc': desc,
                'confidence': confidence,
                'is_correct': is_correct,
                'prob_actual': prob_of_actual,
                'pred_str': pred_str,
                'actual_str': outcome_str
            })
            
        # Update ratings
        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)
        e_away = expected_score(r_away, r_home, -h_adv)
        ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)
        
    db.close()
    
    num_matches = len(validation_records)
    avg_prob_actual = np.mean([r['prob_actual'] for r in validation_records])
    
    print(f"--- Validation Report ---")
    print(f"Total Matches (Last 24 Months): {num_matches}")
    print(f"Average Predicted Probability of Actual Outcome: {avg_prob_actual:.4f}\n")
    
    # Calibration
    # Deciles based on predicted confidence
    deciles = {i: {'count': 0, 'correct': 0, 'sum_conf': 0.0} for i in range(10)}
    for r in validation_records:
        conf = r['confidence']
        d = min(int(conf * 10), 9)
        deciles[d]['count'] += 1
        deciles[d]['sum_conf'] += conf
        if r['is_correct']:
            deciles[d]['correct'] += 1
            
    print("--- Calibration Table (Deciles) ---")
    print(f"{'Decile':<10} | {'Matches':<8} | {'Avg Conf':<10} | {'Observed Acc':<12}")
    print("-" * 50)
    for i in range(10):
        stats = deciles[i]
        if stats['count'] == 0:
            continue
        avg_conf = stats['sum_conf'] / stats['count']
        acc = stats['correct'] / stats['count']
        print(f"{i*10}-{(i+1)*10}%   | {stats['count']:<8} | {avg_conf:.4f}   | {acc:.4f}")
        
    print("\n--- Top 20 Most Confident CORRECT Predictions ---")
    correct_recs = sorted([r for r in validation_records if r['is_correct']], key=lambda x: x['confidence'], reverse=True)[:20]
    for i, r in enumerate(correct_recs):
        print(f"{i+1}. Conf: {r['confidence']:.4f} | {r['pred_str']} | {r['desc']}")

    print("\n--- Top 20 Most Confident INCORRECT Predictions ---")
    incorrect_recs = sorted([r for r in validation_records if not r['is_correct']], key=lambda x: x['confidence'], reverse=True)[:20]
    for i, r in enumerate(incorrect_recs):
        print(f"{i+1}. Conf: {r['confidence']:.4f} | Pred: {r['pred_str']} | Actual: {r['actual_str']} | {r['desc']}")

if __name__ == "__main__":
    main()
