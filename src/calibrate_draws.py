import math
import numpy as np
from collections import defaultdict
from src.database import SessionLocal
from src.models import Team, Match
from src.config import ELO_INITIAL, K_FACTOR, HOME_ADVANTAGE, TOURNAMENT_WEIGHTS, SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
from src.calculate_elo import expected_score, calculate_new_rating

def draw_function(x, a, b):
    # P(Draw) = a * exp(-(x/b)^2)
    # x is the absolute Elo difference
    return a * np.exp(- (x / b)**2)

def main():
    db = SessionLocal()
    teams = db.query(Team).all()
    ratings = {team.name: ELO_INITIAL for team in teams}
    
    matches = db.query(Match).order_by(Match.date).all()
    
    print("Running Elo engine to collect pre-match differences...")
    
    # Store tuples of (abs_diff, is_draw)
    results = []

    for match in matches:
        home = match.home_team
        away = match.away_team

        if home not in ratings or away not in ratings:
            continue
            
        r_home = ratings[home]
        r_away = ratings[away]
        
        h_adv = 0 if match.neutral else HOME_ADVANTAGE
        
        # Effective difference from home perspective
        diff = abs((r_home + h_adv) - r_away)
        
        # Is draw? (in 90 minutes)
        # Even if there was a shootout, it was a draw in regular time.
        # But wait, shootouts ARE draws in regular time.
        is_draw = 1 if match.home_score == match.away_score else 0
        
        results.append((diff, is_draw, match.home_score > match.away_score))
        
        # For updates, we use shootout adjustment to keep Elo identical to V1.0
        if match.home_score > match.away_score:
            s_home, s_away = 1.0, 0.0
        elif match.home_score < match.away_score:
            s_home, s_away = 0.0, 1.0
        else:
            if match.shootout_winner == home:
                s_home, s_away = SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
            elif match.shootout_winner == away:
                s_home, s_away = SHOOTOUT_LOSS_SCORE, SHOOTOUT_WIN_SCORE
            else:
                s_home, s_away = 0.5, 0.5
                
        e_home = expected_score(r_home, r_away, h_adv)
        e_away = expected_score(r_away, r_home, -h_adv)
        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)
        
        ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)
        
    db.close()
    
    # Group by buckets
    buckets = [
        (0, 49),
        (50, 99),
        (100, 149),
        (150, 199),
        (200, 249),
        (250, 299),
        (300, 10000)
    ]
    
    bucket_stats = {b: {'matches': 0, 'draws': 0, 'home_wins': 0, 'away_wins': 0} for b in buckets}
    
    x_data = []
    y_data = []
    
    for diff, draw, h_win in results:
        x_data.append(diff)
        y_data.append(draw)
        for b in buckets:
            if b[0] <= diff <= b[1]:
                bucket_stats[b]['matches'] += 1
                if draw:
                    bucket_stats[b]['draws'] += 1
                elif h_win:
                    bucket_stats[b]['home_wins'] += 1
                else:
                    bucket_stats[b]['away_wins'] += 1
                break
                
    print("\nEmpirical Draw Rates by Elo Difference:")
    print(f"{'Bucket':<10} | {'Matches':<8} | {'Home Win%':<10} | {'Draw%':<10} | {'Away Win%':<10}")
    print("-" * 60)
    
    bucket_midpoints = []
    bucket_draw_rates = []
    
    for b in buckets:
        stats = bucket_stats[b]
        total = stats['matches']
        if total == 0:
            continue
        h_pct = stats['home_wins'] / total * 100
        d_pct = stats['draws'] / total * 100
        a_pct = stats['away_wins'] / total * 100
        b_label = f"{b[0]}-{b[1] if b[1] != 10000 else '+'}"
        print(f"{b_label:<10} | {total:<8} | {h_pct:<10.2f} | {d_pct:<10.2f} | {a_pct:<10.2f}")
        
        midpoint = b[0] + 25 if b[1] != 10000 else 350
        bucket_midpoints.append(midpoint)
        bucket_draw_rates.append(d_pct / 100.0)

    # Fit the function using a simple grid search since scipy is not available
    best_a = 0.25
    best_b = 300
    min_error = float('inf')
    
    for a_val in np.arange(0.20, 0.35, 0.01):
        for b_val in np.arange(150, 600, 5):
            error = 0
            for i in range(len(bucket_midpoints)):
                pred = draw_function(bucket_midpoints[i], a_val, b_val)
                error += (pred - bucket_draw_rates[i])**2
            if error < min_error:
                min_error = error
                best_a = a_val
                best_b = b_val
    
    print(f"\nCalibrated Draw Function: P(Draw) = {best_a:.4f} * exp(-(diff / {best_b:.4f})^2)")

if __name__ == "__main__":
    main()
