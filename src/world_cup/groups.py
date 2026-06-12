"""
Group stage simulation engine.

Simulates round-robin group play using the existing Elo prediction system.
Generates scorelines from predefined outcome distributions (no Poisson model).
"""

import random
from itertools import combinations

from src.prediction import get_match_probabilities
from src.world_cup.models import GroupMatch, TeamStanding, GroupResult


# --- Scoreline distributions ---
# Weighted (scoreline, weight) tuples for each outcome category.
# Weights are relative; they are normalized at sampling time.

WIN_SCORELINES = [
    ((1, 0), 30),
    ((2, 0), 15),
    ((2, 1), 25),
    ((3, 0), 8),
    ((3, 1), 12),
    ((3, 2), 5),
    ((4, 0), 2),
    ((4, 1), 3),
]

DRAW_SCORELINES = [
    ((0, 0), 35),
    ((1, 1), 40),
    ((2, 2), 20),
    ((3, 3), 5),
]


def _sample_scoreline(
    scorelines: list[tuple[tuple[int, int], int]],
) -> tuple[int, int]:
    """Sample a scoreline from a weighted distribution."""
    options, weights = zip(*scorelines)
    return random.choices(options, weights=weights, k=1)[0]


def simulate_group_match(
    elo_a: float, elo_b: float
) -> tuple[int, int]:
    """
    Simulate a single group stage match and return a scoreline.

    Workflow:
        1. Compute win_a / draw / win_b probabilities from Elo.
        2. Sample outcome category (Win A / Draw / Win B).
        3. Sample a concrete scoreline from predefined distributions.

    Parameters:
        elo_a: Elo rating of team A.
        elo_b: Elo rating of team B.

    Returns:
        Tuple (score_a, score_b).
    """
    win_a, draw_prob, win_b = get_match_probabilities(elo_a, elo_b)

    roll = random.random()

    if roll < win_a:
        # Team A wins
        return _sample_scoreline(WIN_SCORELINES)
    elif roll < win_a + draw_prob:
        # Draw
        return _sample_scoreline(DRAW_SCORELINES)
    else:
        # Team B wins — invert the scoreline
        score_b, score_a = _sample_scoreline(WIN_SCORELINES)
        return (score_a, score_b)


def compute_standings(
    teams_with_elos: list[tuple[str, float]],
    matches: list[GroupMatch],
) -> list[TeamStanding]:
    """
    Compute group standings from match results.

    Tie-breaking order:
        1. Points (descending)
        2. Goal Difference (descending)
        3. Goals For (descending)
        4. Elo Rating (descending) — deterministic final breaker

    Parameters:
        teams_with_elos: List of (team_name, elo_rating) tuples.
        matches: List of GroupMatch results.

    Returns:
        Sorted list of TeamStanding objects (best team first).
    """
    elo_lookup = {name: elo for name, elo in teams_with_elos}
    standings = {name: TeamStanding(team=name, elo=elo) for name, elo in teams_with_elos}

    for match in matches:
        a = standings[match.team_a]
        b = standings[match.team_b]

        a.goals_for += match.score_a
        a.goals_against += match.score_b
        b.goals_for += match.score_b
        b.goals_against += match.score_a

        if match.score_a > match.score_b:
            a.wins += 1
            a.points += 3
            b.losses += 1
        elif match.score_a < match.score_b:
            b.wins += 1
            b.points += 3
            a.losses += 1
        else:
            a.draws += 1
            a.points += 1
            b.draws += 1
            b.points += 1

    for s in standings.values():
        s.goal_difference = s.goals_for - s.goals_against

    # Sort by: Points desc, GD desc, GF desc, Elo desc
    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s.points, s.goal_difference, s.goals_for, s.elo),
        reverse=True,
    )

    return sorted_standings


def simulate_group(
    group_name: str,
    teams_with_elos: list[tuple[str, float]],
) -> GroupResult:
    """
    Simulate a complete group stage (round-robin).

    Every team plays every other team exactly once.

    Parameters:
        group_name: Group identifier (e.g. "A").
        teams_with_elos: List of (team_name, elo_rating) for the group.

    Returns:
        GroupResult with sorted standings and all match results.
    """
    matches: list[GroupMatch] = []

    for (team_a, elo_a), (team_b, elo_b) in combinations(teams_with_elos, 2):
        score_a, score_b = simulate_group_match(elo_a, elo_b)
        matches.append(GroupMatch(
            team_a=team_a,
            team_b=team_b,
            score_a=score_a,
            score_b=score_b,
        ))

    standings = compute_standings(teams_with_elos, matches)

    return GroupResult(
        group_name=group_name,
        standings=standings,
        matches=matches,
    )
