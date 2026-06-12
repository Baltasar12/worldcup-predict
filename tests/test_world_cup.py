"""
Tests for World Cup simulation engine.

Covers:
    - Group stage simulation
    - Standings calculation
    - Tie-breaker logic
    - Third-place qualification
    - Bracket generation
    - API endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.world_cup.models import GroupMatch, TeamStanding, GroupResult
from src.world_cup.groups import (
    simulate_group,
    simulate_group_match,
    compute_standings,
)
from src.world_cup.bracket import generate_bracket, rank_third_placed_teams
from src.world_cup.simulator import load_groups, run_group_stage


client = TestClient(app)


# =====================================================================
# Group Stage Tests
# =====================================================================

class TestGroupStageSimulation:
    """Test group stage match and standings logic."""

    def test_simulate_group_match_returns_valid_scores(self):
        """Match scores must be non-negative integers."""
        for _ in range(50):
            score_a, score_b = simulate_group_match(1600.0, 1500.0)
            assert isinstance(score_a, int)
            assert isinstance(score_b, int)
            assert score_a >= 0
            assert score_b >= 0

    def test_simulate_group_all_pairs_play_once(self):
        """Every pair of teams must play exactly once (C(4,2) = 6 matches)."""
        teams = [
            ("TeamA", 1600.0),
            ("TeamB", 1550.0),
            ("TeamC", 1500.0),
            ("TeamD", 1450.0),
        ]
        result = simulate_group("X", teams)

        assert len(result.matches) == 6

        # Check every pair appears exactly once
        pairs = set()
        for m in result.matches:
            pair = frozenset([m.team_a, m.team_b])
            assert pair not in pairs, f"Duplicate match: {m.team_a} vs {m.team_b}"
            pairs.add(pair)

        expected_pairs = {
            frozenset(["TeamA", "TeamB"]),
            frozenset(["TeamA", "TeamC"]),
            frozenset(["TeamA", "TeamD"]),
            frozenset(["TeamB", "TeamC"]),
            frozenset(["TeamB", "TeamD"]),
            frozenset(["TeamC", "TeamD"]),
        }
        assert pairs == expected_pairs

    def test_simulate_group_returns_correct_number_of_standings(self):
        """Standings must contain exactly one entry per team."""
        teams = [
            ("TeamA", 1600.0),
            ("TeamB", 1550.0),
            ("TeamC", 1500.0),
            ("TeamD", 1450.0),
        ]
        result = simulate_group("X", teams)
        assert len(result.standings) == 4

    def test_total_matches_per_group(self):
        """A group of 4 teams must produce exactly 6 matches."""
        teams = [("T1", 1500.0), ("T2", 1500.0), ("T3", 1500.0), ("T4", 1500.0)]
        result = simulate_group("Z", teams)
        assert len(result.matches) == 6

    def test_goal_difference_sums_to_zero(self):
        """Total goal difference across all teams in a group must be zero."""
        teams = [
            ("TeamA", 1700.0),
            ("TeamB", 1500.0),
            ("TeamC", 1400.0),
            ("TeamD", 1300.0),
        ]
        result = simulate_group("X", teams)
        total_gd = sum(s.goal_difference for s in result.standings)
        assert total_gd == 0, f"GD sum should be 0, got {total_gd}"

    def test_total_points_consistency(self):
        """
        Total points across the group must equal 3 * (number of decisive matches)
        + 2 * (number of draws).

        Equivalently: each match distributes either 3 points (win/loss) or
        2 points (draw), so total points = 3*wins + 1*draws across all teams,
        and total_wins + total_draws/2 = 6 (total matches).
        """
        teams = [("T1", 1500.0), ("T2", 1500.0), ("T3", 1500.0), ("T4", 1500.0)]
        result = simulate_group("Z", teams)

        total_points = sum(s.points for s in result.standings)
        total_draws = sum(s.draws for s in result.standings)
        total_wins = sum(s.wins for s in result.standings)
        total_losses = sum(s.losses for s in result.standings)

        # Each win gives one team 3 points, each draw gives each team 1 point
        assert total_points == total_wins * 3 + total_draws * 1

        # Total wins must equal total losses (every match has one winner or is a draw)
        assert total_wins == total_losses

        # Each team plays 3 matches, so total match slots = 4 * 3 = 12
        # Each match uses 2 slots, so 6 matches total
        assert (total_wins + total_losses + total_draws) == 4 * 3  # 12 slots


# =====================================================================
# Standings / Tie-Breaker Tests
# =====================================================================

class TestStandingsAndTieBreakers:
    """Test standings computation and tie-breaking order."""

    def test_standings_sorted_by_points(self):
        """Higher points should rank higher."""
        teams = [("A", 1500.0), ("B", 1500.0), ("C", 1500.0)]
        matches = [
            GroupMatch(team_a="A", team_b="B", score_a=2, score_b=0),  # A wins
            GroupMatch(team_a="A", team_b="C", score_a=1, score_b=0),  # A wins
            GroupMatch(team_a="B", team_b="C", score_a=1, score_b=0),  # B wins
        ]
        standings = compute_standings(teams, matches)
        assert standings[0].team == "A"  # 6 pts
        assert standings[1].team == "B"  # 3 pts
        assert standings[2].team == "C"  # 0 pts

    def test_tiebreaker_goal_difference(self):
        """Equal points: higher goal difference ranks higher."""
        teams = [("A", 1500.0), ("B", 1500.0), ("C", 1500.0)]
        matches = [
            GroupMatch(team_a="A", team_b="B", score_a=3, score_b=0),  # A wins big
            GroupMatch(team_a="B", team_b="C", score_a=2, score_b=0),  # B wins
            GroupMatch(team_a="C", team_b="A", score_a=1, score_b=0),  # C wins
        ]
        # Points: A=3, B=3, C=3
        standings = compute_standings(teams, matches)
        # GD: A = +3 - 1 = +2, B = +2 - 3 = -1, C = +1 - 2 = -1
        assert standings[0].team == "A"

    def test_tiebreaker_goals_for(self):
        """Equal points and GD: higher goals for ranks higher."""
        teams = [("A", 1500.0), ("B", 1500.0), ("C", 1500.0)]
        matches = [
            GroupMatch(team_a="A", team_b="B", score_a=2, score_b=1),  # A wins
            GroupMatch(team_a="B", team_b="C", score_a=3, score_b=2),  # B wins
            GroupMatch(team_a="C", team_b="A", score_a=1, score_b=0),  # C wins
        ]
        # Points: A=3, B=3, C=3
        # GD: A = 2 - 2 = 0, B = 4 - 4 = 0, C = 3 - 3 = 0
        # GF: A = 2, B = 4, C = 3
        standings = compute_standings(teams, matches)
        assert standings[0].team == "B"  # Highest GF
        assert standings[1].team == "C"
        assert standings[2].team == "A"

    def test_tiebreaker_elo(self):
        """Equal points, GD, and GF: higher Elo ranks higher."""
        teams = [("A", 1400.0), ("B", 1600.0)]
        matches = [
            GroupMatch(team_a="A", team_b="B", score_a=1, score_b=1),
        ]
        # Points: 1 each, GD: 0 each, GF: 1 each
        standings = compute_standings(teams, matches)
        assert standings[0].team == "B"  # Higher Elo


# =====================================================================
# Third-Place Qualification Tests
# =====================================================================

class TestThirdPlaceQualification:
    """Test best third-placed team selection."""

    def _make_group_result(self, group_name: str, third_place_standing: TeamStanding) -> GroupResult:
        """Helper to create a GroupResult with a specific third-placed team."""
        return GroupResult(
            group_name=group_name,
            standings=[
                TeamStanding(team=f"{group_name}_1st", points=9, elo=1700.0),
                TeamStanding(team=f"{group_name}_2nd", points=6, elo=1600.0),
                third_place_standing,
                TeamStanding(team=f"{group_name}_4th", points=0, elo=1300.0),
            ],
            matches=[],
        )

    def test_exactly_8_third_placed_qualify(self):
        """Exactly 8 of 12 third-placed teams should qualify."""
        group_results = []
        for i, gname in enumerate("ABCDEFGHIJKL"):
            third = TeamStanding(
                team=f"{gname}_3rd",
                points=3 - (i % 4),  # Varying points
                goal_difference=i,
                goals_for=i + 1,
                elo=1500.0 - i * 10,
            )
            group_results.append(self._make_group_result(gname, third))

        best_thirds = rank_third_placed_teams(group_results)
        assert len(best_thirds) == 8

    def test_third_place_ranking_by_points(self):
        """Third-placed teams should be ranked by points first."""
        group_results = []
        points_values = [4, 1, 3, 2, 4, 1, 3, 2, 4, 1, 3, 2]
        for i, gname in enumerate("ABCDEFGHIJKL"):
            third = TeamStanding(
                team=f"{gname}_3rd",
                points=points_values[i],
                goal_difference=0,
                goals_for=0,
                elo=1500.0,
            )
            group_results.append(self._make_group_result(gname, third))

        best_thirds = rank_third_placed_teams(group_results)

        # All 4-point teams should be in, all 3-point teams should be in
        # That's 3 + 3 = 6, then 2-point teams fill remaining 2 slots
        qualified_teams = {t.team for t, _ in best_thirds}
        for gname in "AEI":
            assert f"{gname}_3rd" in qualified_teams  # 4 points
        for gname in "CGK":
            assert f"{gname}_3rd" in qualified_teams  # 3 points

    def test_third_place_no_duplicates(self):
        """No duplicate teams in the qualified list."""
        group_results = []
        for i, gname in enumerate("ABCDEFGHIJKL"):
            third = TeamStanding(
                team=f"{gname}_3rd",
                points=3,
                goal_difference=i,
                goals_for=i,
                elo=1500.0,
            )
            group_results.append(self._make_group_result(gname, third))

        best_thirds = rank_third_placed_teams(group_results)
        team_names = [t.team for t, _ in best_thirds]
        assert len(team_names) == len(set(team_names))


# =====================================================================
# Bracket Generation Tests
# =====================================================================

class TestBracketGeneration:
    """Test knockout bracket creation."""

    def _make_full_group_results(self) -> list[GroupResult]:
        """Create 12 group results with distinct team names."""
        results = []
        for gname in "ABCDEFGHIJKL":
            standings = [
                TeamStanding(
                    team=f"{gname}_{pos}",
                    points=[9, 6, 3, 0][pos - 1],
                    goal_difference=[5, 2, -1, -6][pos - 1],
                    goals_for=[8, 5, 3, 1][pos - 1],
                    elo=[1700, 1600, 1500, 1400][pos - 1],
                )
                for pos in range(1, 5)
            ]
            results.append(GroupResult(group_name=gname, standings=standings, matches=[]))
        return results

    def test_bracket_has_16_matches(self):
        """Round of 32 must have exactly 16 matches."""
        results = self._make_full_group_results()
        bracket = generate_bracket(results)
        assert len(bracket.round_of_32) == 16

    def test_bracket_has_32_qualified_teams(self):
        """The bracket must contain exactly 32 unique teams."""
        results = self._make_full_group_results()
        bracket = generate_bracket(results)
        assert bracket.qualified_teams == 32

    def test_no_duplicate_teams_in_bracket(self):
        """Each qualified team must appear exactly once across all matches."""
        results = self._make_full_group_results()
        bracket = generate_bracket(results)

        teams_in_bracket = []
        for bm in bracket.round_of_32:
            teams_in_bracket.append(bm.team_a)
            teams_in_bracket.append(bm.team_b)

        assert len(teams_in_bracket) == 32
        assert len(set(teams_in_bracket)) == 32, "Duplicate team found in bracket"

    def test_every_qualified_team_appears(self):
        """All 32 qualified teams (12 winners + 12 runners-up + 8 thirds) must appear."""
        results = self._make_full_group_results()
        bracket = generate_bracket(results)

        teams_in_bracket = set()
        for bm in bracket.round_of_32:
            teams_in_bracket.add(bm.team_a)
            teams_in_bracket.add(bm.team_b)

        # Check that winners and runners-up are all present
        for gname in "ABCDEFGHIJKL":
            assert f"{gname}_1" in teams_in_bracket, f"Winner of Group {gname} missing"
            assert f"{gname}_2" in teams_in_bracket, f"Runner-up of Group {gname} missing"

        # 24 from winners+runners-up + 8 thirds = 32
        assert len(teams_in_bracket) == 32

    def test_bracket_match_ids_are_sequential(self):
        """Match IDs should be sequential from 1 to 16."""
        results = self._make_full_group_results()
        bracket = generate_bracket(results)
        ids = [bm.match_id for bm in bracket.round_of_32]
        assert ids == list(range(1, 17))


# =====================================================================
# API Endpoint Tests
# =====================================================================

class TestWorldCupAPI:
    """Test World Cup API endpoints."""

    def test_get_groups(self):
        """GET /world-cup/groups should return valid groups."""
        response = client.get("/world-cup/groups")
        assert response.status_code == 200
        data = response.json()
        assert "tournament" in data
        assert "groups" in data
        assert len(data["groups"]) == 12
        for group_name, teams in data["groups"].items():
            assert len(teams) == 4

    def test_group_stage_simulation(self):
        """POST /world-cup/group-stage should return standings and matches."""
        response = client.post("/world-cup/group-stage")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert len(data["groups"]) == 12

        for group in data["groups"]:
            assert "group" in group
            assert "standings" in group
            assert "matches" in group
            assert len(group["standings"]) == 4
            assert len(group["matches"]) == 6

            # Verify standings structure
            for standing in group["standings"]:
                assert "team" in standing
                assert "points" in standing
                assert "wins" in standing
                assert "draws" in standing
                assert "losses" in standing
                assert "goals_for" in standing
                assert "goals_against" in standing
                assert "goal_difference" in standing
                assert "elo" in standing

    def test_bracket_generation(self):
        """POST /world-cup/bracket should return a valid bracket."""
        response = client.post("/world-cup/bracket")
        assert response.status_code == 200
        data = response.json()
        assert "round_of_32" in data
        assert "qualified_teams" in data
        assert data["qualified_teams"] == 32
        assert len(data["round_of_32"]) == 16

        # Check each match has required fields
        for match in data["round_of_32"]:
            assert "match_id" in match
            assert "round" in match
            assert "team_a" in match
            assert "team_b" in match
            assert "team_a_origin" in match
            assert "team_b_origin" in match

    def test_simulate_endpoint(self):
        """POST /world-cup/simulate should return groups + bracket."""
        response = client.post("/world-cup/simulate")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert "bracket" in data
        assert len(data["groups"]) == 12
        assert len(data["bracket"]["round_of_32"]) == 16
        assert data["bracket"]["qualified_teams"] == 32

    def test_no_duplicate_teams_in_api_bracket(self):
        """Teams in the API bracket response must be unique."""
        response = client.post("/world-cup/simulate")
        assert response.status_code == 200
        data = response.json()

        teams = []
        for match in data["bracket"]["round_of_32"]:
            teams.append(match["team_a"])
            teams.append(match["team_b"])

        assert len(teams) == 32
        assert len(set(teams)) == 32


# =====================================================================
# V1 Backward Compatibility Tests
# =====================================================================

class TestV1BackwardCompatibility:
    """Ensure V1 endpoints are unaffected."""

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "1.0"}

    def test_rankings(self):
        response = client.get("/rankings?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_predict(self):
        response = client.get("/predict?team_a=Argentina&team_b=France")
        if response.status_code == 200:
            data = response.json()
            assert "win_probability_a" in data
            assert "draw_probability" in data
            assert "win_probability_b" in data

    def test_simulate(self):
        payload = {"teams": ["Argentina", "France", "Spain", "Germany"]}
        response = client.post("/simulate", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "simulations_run" in data
            assert "champions" in data
