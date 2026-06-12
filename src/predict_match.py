import sys
from src.database import SessionLocal
from src.models import Team, TeamRating
from src.calculate_elo import expected_score

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m src.predict_match <Team A> <Team B>")
        return

    team_a_name = sys.argv[1]
    team_b_name = sys.argv[2]

    db = SessionLocal()

    team_a = db.query(Team).filter(Team.name == team_a_name).first()
    team_b = db.query(Team).filter(Team.name == team_b_name).first()

    if not team_a or not team_b:
        print("Error: One or both teams not found.")
        return

    rating_a_obj = db.query(TeamRating).filter(TeamRating.team_id == team_a.id).first()
    rating_b_obj = db.query(TeamRating).filter(TeamRating.team_id == team_b.id).first()

    rating_a = rating_a_obj.rating if rating_a_obj else 1500
    rating_b = rating_b_obj.rating if rating_b_obj else 1500

    # Elo Probabilities (neutral venue)
    prob_a = expected_score(rating_a, rating_b, 0)
    prob_b = expected_score(rating_b, rating_a, 0)

    print(f"{team_a_name} - Elo: {rating_a:.1f}")
    print(f"{team_b_name} - Elo: {rating_b:.1f}\n")
    print(f"Win Probability {team_a_name}: {prob_a * 100:.2f}%")
    print(f"Win Probability {team_b_name}: {prob_b * 100:.2f}%")

    db.close()

if __name__ == "__main__":
    main()
