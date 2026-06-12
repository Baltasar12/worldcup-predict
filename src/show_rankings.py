from src.database import SessionLocal
from src.models import Team, TeamRating

def main():
    db = SessionLocal()

    # Query ratings and join with team
    results = db.query(TeamRating, Team).join(Team, TeamRating.team_id == Team.id).order_by(TeamRating.rating.desc()).limit(20).all()

    if not results:
        print("No rankings found. Run calculate_elo first.")
        return

    print(f"{'Rank':<5} | {'Team':<30} | {'Elo':<10}")
    print("-" * 50)

    for i, (rating_obj, team_obj) in enumerate(results, 1):
        print(f"{i:<5} | {team_obj.name:<30} | {rating_obj.rating:.1f}")

    db.close()

if __name__ == "__main__":
    main()
