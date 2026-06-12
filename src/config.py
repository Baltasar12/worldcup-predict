import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/football.db")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "results.csv")
SHOOTOUTS_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "shootouts.csv")

# Elo Parameters
ELO_INITIAL = 1500
K_FACTOR = 30
HOME_ADVANTAGE = 80

# Phase 2 Parameters
SHOOTOUT_WIN_SCORE = 0.75
SHOOTOUT_LOSS_SCORE = 0.25

# Tournament Weighting
TOURNAMENT_WEIGHTS = {
    "FIFA World Cup": 1.5,
    "UEFA Euro": 1.4,
    "Copa América": 1.4,
    "FIFA World Cup qualification": 1.2,
    "Friendly": 1.0
}
