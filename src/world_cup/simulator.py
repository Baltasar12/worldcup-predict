"""
High-level simulation orchestration.

Coordinates group stage and bracket generation for a single
World Cup simulation run.
"""

import json
import os
import random
from collections import defaultdict

from src.world_cup.models import GroupResult, Bracket, BracketMatch
from src.world_cup.groups import simulate_group
from src.world_cup.bracket import generate_bracket
from src.prediction import get_match_probabilities


DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "world_cup_2026.json"
)


def load_groups() -> dict:
    """Load World Cup 2026 groups configuration."""
    with open("data/world_cup_2026_groups.json", "r", encoding="utf-8") as f:
        return json.load(f)


def run_group_stage(
    groups: dict[str, list[str]],
    elo_lookup: dict[str, float],
) -> list[GroupResult]:
    """
    Simulate the group stage for all groups.

    Parameters:
        groups: Dict mapping group name to list of team names.
        elo_lookup: Dict mapping team name to current Elo rating.

    Returns:
        List of GroupResult objects (one per group), sorted by group name.
    """
    results = []
    for group_name in sorted(groups.keys()):
        teams = groups[group_name]
        teams_with_elos = [
            (team, elo_lookup.get(team, 1500.0)) for team in teams
        ]
        result = simulate_group(group_name, teams_with_elos)
        results.append(result)

    return results


def run_single_simulation(
    groups: dict[str, list[str]],
    elo_lookup: dict[str, float],
) -> dict:
    """
    Run a complete single simulation: group stage + bracket generation + bracket resolution.
    """
    group_results = run_group_stage(groups, elo_lookup)
    bracket = generate_bracket(group_results)

    def play_matches(matches, next_round_name):
        next_matches = []
        for i in range(0, len(matches), 2):
            if i + 1 >= len(matches):
                break
            m1 = matches[i]
            m2 = matches[i+1]
            w1 = simulate_knockout_match(m1.team_a, m1.team_b, elo_lookup)
            w2 = simulate_knockout_match(m2.team_a, m2.team_b, elo_lookup)
            
            next_matches.append(BracketMatch(
                match_id=m1.match_id * 100 + m2.match_id,
                round_name=next_round_name,
                team_a=w1,
                team_b=w2,
                team_a_origin=f"Winner Match {m1.match_id}",
                team_b_origin=f"Winner Match {m2.match_id}",
            ))
        return next_matches

    bracket.round_of_16 = play_matches(bracket.round_of_32, "Round of 16")
    bracket.quarterfinals = play_matches(bracket.round_of_16, "Quarterfinal")
    bracket.semifinals = play_matches(bracket.quarterfinals, "Semifinal")
    bracket.final = play_matches(bracket.semifinals, "Final")
    
    # The final has 1 match, we simulate it to find the champion
    if bracket.final:
        final_match = bracket.final[0]
        bracket.champion = simulate_knockout_match(final_match.team_a, final_match.team_b, elo_lookup)

    return {
        "group_results": group_results,
        "bracket": bracket,
    }


def simulate_knockout_match(team_a: str, team_b: str, elo_lookup: dict[str, float]) -> str:
    """
    Simulates a single knockout match.
    Draws are resolved by a 50/50 penalty shootout.
    """
    elo_a = elo_lookup.get(team_a, 1500.0)
    elo_b = elo_lookup.get(team_b, 1500.0)
    
    win_a, draw_prob, win_b = get_match_probabilities(elo_a, elo_b)
    
    roll = random.random()
    if roll < win_a:
        return team_a
    elif roll < win_a + win_b:
        return team_b
    else:
        # Draw, resolved by simple 50/50 penalty shootout
        return random.choice([team_a, team_b])

def simulate_round(teams: list[str], elo_lookup: dict[str, float]) -> list[str]:
    """
    Simulates a knockout round.
    Takes a list of teams (paired adjacently) and returns the winners.
    """
    winners = []
    for i in range(0, len(teams), 2):
        winner = simulate_knockout_match(teams[i], teams[i+1], elo_lookup)
        winners.append(winner)
    return winners

def run_monte_carlo_simulation(simulations: int, seed: int | None, groups: dict[str, list[str]], elo_lookup: dict[str, float]) -> list[dict]:
    """
    Runs a full Monte Carlo simulation of the World Cup.
    """
    if seed is not None:
        random.seed(seed)

    stats = defaultdict(lambda: {
        "qualified_from_groups": 0,
        "round_of_16": 0,
        "quarterfinal": 0,
        "semifinal": 0,
        "final": 0,
        "champion": 0
    })

    # Pre-collect all teams so we can report on teams that didn't even make R32
    for group_teams in groups.values():
        for team in group_teams:
            stats[team]  # Initialize the dict
            
    for _ in range(simulations):
        # 1. Group Stage
        group_results = run_group_stage(groups, elo_lookup)
        bracket = generate_bracket(group_results)
        
        # Extract the 32 qualified teams in match order
        r32_teams = []
        for match in bracket.round_of_32:
            r32_teams.append(match.team_a)
            r32_teams.append(match.team_b)
            
        for t in r32_teams:
            stats[t]["qualified_from_groups"] += 1
            
        # 2. Round of 32 -> Round of 16
        r16_teams = simulate_round(r32_teams, elo_lookup)
        for t in r16_teams:
            stats[t]["round_of_16"] += 1
            
        # 3. Round of 16 -> Quarterfinals
        qf_teams = simulate_round(r16_teams, elo_lookup)
        for t in qf_teams:
            stats[t]["quarterfinal"] += 1
            
        # 4. Quarterfinals -> Semifinals
        sf_teams = simulate_round(qf_teams, elo_lookup)
        for t in sf_teams:
            stats[t]["semifinal"] += 1
            
        # 5. Semifinals -> Final
        finalists = simulate_round(sf_teams, elo_lookup)
        for t in finalists:
            stats[t]["final"] += 1
            
        # 6. Final -> Champion
        champion = simulate_round(finalists, elo_lookup)[0]
        stats[champion]["champion"] += 1

    # Clear the seed so we don't accidentally affect subsequent calls
    if seed is not None:
        random.seed()

    # Convert to percentages
    results = []
    for team, counts in stats.items():
        results.append({
            "team": team,
            "qualified_from_groups": round((counts["qualified_from_groups"] / simulations) * 100, 1),
            "round_of_16": round((counts["round_of_16"] / simulations) * 100, 1),
            "quarterfinal": round((counts["quarterfinal"] / simulations) * 100, 1),
            "semifinal": round((counts["semifinal"] / simulations) * 100, 1),
            "final": round((counts["final"] / simulations) * 100, 1),
            "champion": round((counts["champion"] / simulations) * 100, 1),
        })

    # Sort descending by champion probability
    results.sort(key=lambda x: x["champion"], reverse=True)
    
    return results
