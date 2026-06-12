"""
High-level simulation orchestration.

Coordinates group stage and bracket generation for a single
World Cup simulation run.
"""

import json
import os

from src.world_cup.models import GroupResult, Bracket
from src.world_cup.groups import simulate_group
from src.world_cup.bracket import generate_bracket


DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "world_cup_2026.json"
)


def load_groups() -> dict:
    """
    Load World Cup group configuration from the JSON dataset.

    Returns:
        Dict with keys 'tournament' and 'groups'.
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
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
    Run a complete single simulation: group stage + bracket generation.

    Parameters:
        groups: Dict mapping group name to list of team names.
        elo_lookup: Dict mapping team name to current Elo rating.

    Returns:
        Dict with 'group_results' and 'bracket'.
    """
    group_results = run_group_stage(groups, elo_lookup)
    bracket = generate_bracket(group_results)

    return {
        "group_results": group_results,
        "bracket": bracket,
    }
