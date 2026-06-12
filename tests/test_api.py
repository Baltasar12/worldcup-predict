import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0"}

def test_rankings():
    response = client.get("/rankings?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    if len(data) > 0:
        assert "team" in data[0]
        assert "elo" in data[0]

def test_predict_match():
    response = client.get("/predict?team_a=Argentina&team_b=France")
    # If the DB has Argentina and France
    if response.status_code == 200:
        data = response.json()
        assert data["team_a"] == "Argentina"
        assert data["team_b"] == "France"
        assert "win_probability_a" in data
        assert "draw_probability" in data
        assert "win_probability_b" in data
        assert "favorite" in data
        assert "elo_a" in data
        assert "elo_b" in data
    else:
        assert response.status_code == 404

def test_simulate_tournament():
    payload = {
        "teams": ["Argentina", "France", "Spain", "Germany"]
    }
    response = client.post("/simulate", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert "simulations_run" in data
        assert "champions" in data
        assert len(data["champions"]) <= 4
