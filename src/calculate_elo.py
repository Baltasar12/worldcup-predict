import os
from datetime import datetime
from src.database import SessionLocal
from src.models import Team, Match, TeamRating
from src.config import (
    ELO_INITIAL, K_FACTOR, HOME_ADVANTAGE, TOURNAMENT_WEIGHTS,
    SHOOTOUT_WIN_SCORE, SHOOTOUT_LOSS_SCORE
)

def expected_score(rating_a, rating_b, home_advantage=0):
    import math
    return 1 / (1 + math.pow(10, (rating_b - rating_a - home_advantage) / 400))

def calculate_new_rating(rating, expected, actual, k_factor, weight):
    return rating + k_factor * weight * (actual - expected)

def main():
    db = SessionLocal()

    # Load teams
    teams = db.query(Team).all()
    team_ratings = {team.name: ELO_INITIAL for team in teams}
    team_id_map = {team.name: team.id for team in teams}

    print("Loading matches...")
    matches = db.query(Match).order_by(Match.date).all()
    
    if not matches:
        print("No matches found. Run import_dataset first.")
        return

    print(f"Calculating Elo for {len(matches)} matches...")

    for match in matches:
        home = match.home_team
        away = match.away_team

        if home not in team_ratings or away not in team_ratings:
            continue

        r_home = team_ratings[home]
        r_away = team_ratings[away]

        # Determine actual scores
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

        # Determine home advantage
        h_adv = 0 if match.neutral else HOME_ADVANTAGE

        e_home = expected_score(r_home, r_away, h_adv)
        e_away = expected_score(r_away, r_home, -h_adv)

        weight = TOURNAMENT_WEIGHTS.get(match.tournament, 1.0)

        # Update Elo ratings
        team_ratings[home] = calculate_new_rating(r_home, e_home, s_home, K_FACTOR, weight)
        team_ratings[away] = calculate_new_rating(r_away, e_away, s_away, K_FACTOR, weight)

    print("Saving final ratings to database...")
    db.query(TeamRating).delete()
    db.commit()

    ratings_to_insert = []
    calc_date = datetime.now().date()
    
    for team_name in team_ratings.keys():
        t_id = team_id_map[team_name]
        ratings_to_insert.append(TeamRating(
            team_id=t_id,
            rating=team_ratings[team_name],
            calculated_at=calc_date
        ))

    db.bulk_save_objects(ratings_to_insert)
    db.commit()
    db.close()
    
    print("Elo calculation completed.")

if __name__ == "__main__":
    main()
