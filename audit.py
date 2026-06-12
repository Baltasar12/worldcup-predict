import pandas as pd
from src.database import SessionLocal
from src.models import Team

db = SessionLocal()
db_teams = {t.name for t in db.query(Team).all()}
db.close()

df = pd.read_csv('datasets/results.csv')
csv_teams = set(df['home_team']).union(set(df['away_team']))

check_names = ["USA", "IR Iran", "Korea Republic", "Côte d'Ivoire", "Bosnia-Herzegovina", "Czechia", "United States", "Iran", "South Korea", "Ivory Coast", "Bosnia and Herzegovina", "Czech Republic"]

print("--- DB Teams ---")
for t in check_names:
    print(f"{t}: {t in db_teams}")

print("\n--- CSV Teams ---")
for t in check_names:
    print(f"{t}: {t in csv_teams}")
