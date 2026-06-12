import sys
import random
from collections import defaultdict
from src.database import SessionLocal
from src.models import Team, TeamRating
from src.calculate_elo import expected_score

def simulate_match(rating_a, rating_b):
    prob_a = expected_score(rating_a, rating_b, 0)
    return 'A' if random.random() < prob_a else 'B'

def simulate_knockout(teams_with_ratings):
    current_round = teams_with_ratings[:]
    
    while len(current_round) > 1:
        next_round = []
        for i in range(0, len(current_round), 2):
            if i + 1 >= len(current_round):
                next_round.append(current_round[i])
            else:
                team_a, rat_a = current_round[i]
                team_b, rat_b = current_round[i+1]
                winner = simulate_match(rat_a, rat_b)
                if winner == 'A':
                    next_round.append(current_round[i])
                else:
                    next_round.append(current_round[i+1])
        current_round = next_round
        
    return current_round[0][0]

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.simulate_tournament <Team1> <Team2> ...")
        return

    team_names = sys.argv[1:]
    simulations = 10000

    db = SessionLocal()
    teams = db.query(Team).filter(Team.name.in_(team_names)).all()
    
    if len(teams) != len(team_names):
        found_names = [t.name for t in teams]
        missing = set(team_names) - set(found_names)
        print(f"Error: Could not find teams: {', '.join(missing)}")
        return
        
    ratings = {r.team_id: r.rating for r in db.query(TeamRating).filter(TeamRating.team_id.in_([t.id for t in teams])).all()}
    
    teams_with_ratings = []
    for team in teams:
        r = ratings.get(team.id, 1500)
        teams_with_ratings.append((team.name, r))

    print(f"Simulating {simulations} tournaments with {len(teams_with_ratings)} teams...")

    champions = defaultdict(int)

    for _ in range(simulations):
        bracket = teams_with_ratings[:]
        random.shuffle(bracket)
        winner = simulate_knockout(bracket)
        champions[winner] += 1

    print("\nTeam | Champion %")
    print("-" * 25)
    
    sorted_champions = sorted(champions.items(), key=lambda x: x[1], reverse=True)
    
    for team_name, wins in sorted_champions:
        win_pct = (wins / simulations) * 100
        print(f"{team_name:<15} {win_pct:.1f}%")

    db.close()

if __name__ == "__main__":
    main()
