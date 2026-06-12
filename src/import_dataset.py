import os
import pandas as pd
from datetime import datetime
from src.database import engine, SessionLocal
from src.models import Base, Team, Match
from src.config import DATASET_PATH

def init_db():
    Base.metadata.create_all(bind=engine)

def main():
    print(f"Loading dataset from {DATASET_PATH}...")
    if not os.path.exists(DATASET_PATH):
        print(f"Error: File not found at {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)

    required_columns = [
        'date', 'home_team', 'away_team', 'home_score', 'away_score', 
        'tournament', 'city', 'country', 'neutral'
    ]

    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Required column '{col}' is missing.")
            return

    # Drop null scores
    df = df.dropna(subset=['home_score', 'away_score'])

    # Convert date
    df['date'] = pd.to_datetime(df['date']).dt.date
    # Neutral should be boolean
    df['neutral'] = df['neutral'].astype(bool)

    # Convert scores to int
    df['home_score'] = df['home_score'].astype(int)
    df['away_score'] = df['away_score'].astype(int)

    print("Initializing database...")
    os.makedirs(os.path.dirname(engine.url.database.split("///")[-1]), exist_ok=True)
    init_db()

    db = SessionLocal()

    # Get unique teams
    print("Extracting unique teams...")
    unique_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())

    # Insert teams
    existing_teams_obj = db.query(Team).all()
    existing_teams = {t.name: t for t in existing_teams_obj}
    new_teams = []
    for team_name in unique_teams:
        if team_name not in existing_teams:
            new_teams.append(Team(name=team_name))

    if new_teams:
        db.add_all(new_teams)
        db.commit()
        print(f"Inserted {len(new_teams)} new teams.")

    # Insert matches
    print("Inserting matches...")
    # Check existing matches to avoid duplicates
    existing_match_count = db.query(Match).count()
    if existing_match_count > 0:
        print(f"Database already contains {existing_match_count} matches. Clearing matches to reload.")
        db.query(Match).delete()
        db.commit()

    # Load shootouts
    shootouts_path = os.path.join(os.path.dirname(DATASET_PATH), "shootouts.csv")
    shootout_map = {}
    if os.path.exists(shootouts_path):
        df_shoot = pd.read_csv(shootouts_path)
        for _, row in df_shoot.iterrows():
            key = (str(row['date']), row['home_team'], row['away_team'])
            shootout_map[key] = row['winner']

    # Bulk insert
    matches_to_insert = []
    for _, row in df.iterrows():
        key = (str(row['date']), row['home_team'], row['away_team'])
        s_winner = shootout_map.get(key)
        matches_to_insert.append(Match(
            date=row['date'],
            home_team=row['home_team'],
            away_team=row['away_team'],
            home_score=row['home_score'],
            away_score=row['away_score'],
            tournament=row['tournament'],
            city=row['city'],
            country=row['country'],
            neutral=row['neutral'],
            shootout_winner=s_winner
        ))

    # Bulk save to speed up
    batch_size = 10000
    for i in range(0, len(matches_to_insert), batch_size):
        db.bulk_save_objects(matches_to_insert[i:i+batch_size])
        db.commit()
        print(f"Inserted matches batch {i // batch_size + 1}")

    db.close()
    print("Import completed.")

if __name__ == "__main__":
    main()
