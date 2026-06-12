"""
Knockout bracket generation for FIFA World Cup 2026.

Implements the 48-team format:
    - 12 groups of 4
    - Top 2 from each group qualify (24 teams)
    - Best 8 third-placed teams qualify (8 teams)
    - Total: 32 teams in Round of 32

The bracket pairing follows a cross-group seeding pattern to avoid
same-group rematches in the Round of 32 where possible.
"""

from src.world_cup.models import GroupResult, TeamStanding, BracketMatch, Bracket


def rank_third_placed_teams(
    group_results: list[GroupResult],
) -> list[tuple[TeamStanding, str]]:
    """
    Rank all third-placed teams and return the best 8.

    Ranking criteria (in order):
        1. Points (descending)
        2. Goal Difference (descending)
        3. Goals For (descending)
        4. Elo Rating (descending)

    Parameters:
        group_results: All 12 group results.

    Returns:
        List of (TeamStanding, group_name) tuples for the 8 best
        third-placed teams, sorted from best to worst.
    """
    third_placed = []
    for gr in group_results:
        if len(gr.standings) >= 3:
            third_placed.append((gr.standings[2], gr.group_name))

    third_placed.sort(
        key=lambda x: (
            x[0].points,
            x[0].goal_difference,
            x[0].goals_for,
            x[0].elo,
        ),
        reverse=True,
    )

    return third_placed[:8]


def generate_bracket(group_results: list[GroupResult]) -> Bracket:
    """
    Generate the Round of 32 knockout bracket.

    Collects:
        - 12 group winners (1st place from each group)
        - 12 runners-up (2nd place from each group)
        - 8 best third-placed teams

    Pairing pattern for Round of 32 (16 matches):
        - Group winners are seeded against third-placed qualifiers
          or runners-up from distant groups.
        - Runners-up face runners-up or third-placed from other groups.

    The specific pairing ensures cross-group matchups. The pattern used:

        Match  1: 1A vs 3rd-best-8
        Match  2: 2A vs 2F
        Match  3: 1B vs 3rd-best-7
        Match  4: 2B vs 2E
        Match  5: 1C vs 3rd-best-6
        Match  6: 2C vs 2D
        Match  7: 1D vs 3rd-best-5
        Match  8: 2G vs 2L
        Match  9: 1E vs 3rd-best-4
        Match 10: 2H vs 2K
        Match 11: 1F vs 3rd-best-3
        Match 12: 2I vs 2J
        Match 13: 1G vs 3rd-best-2
        Match 14: 1H vs 3rd-best-1
        Match 15: 1I vs 1L
        Match 16: 1J vs 1K

    Parameters:
        group_results: All 12 group results with sorted standings.

    Returns:
        Bracket object with 16 Round of 32 matches.
    """
    # Build lookup: group_name -> standings
    groups = {gr.group_name: gr.standings for gr in group_results}

    # Collect winners and runners-up
    winners = {}
    runners_up = {}
    for gname, standings in groups.items():
        winners[gname] = standings[0]
        runners_up[gname] = standings[1]

    # Get best 8 third-placed teams
    best_thirds = rank_third_placed_teams(group_results)

    # Build the 16 Round of 32 pairings
    # Format: (team_a_standing, origin_a, team_b_standing, origin_b)
    pairings = [
        (winners["A"], "1A", best_thirds[7][0], f"3rd-{best_thirds[7][1]}"),
        (runners_up["A"], "2A", runners_up["F"], "2F"),
        (winners["B"], "1B", best_thirds[6][0], f"3rd-{best_thirds[6][1]}"),
        (runners_up["B"], "2B", runners_up["E"], "2E"),
        (winners["C"], "1C", best_thirds[5][0], f"3rd-{best_thirds[5][1]}"),
        (runners_up["C"], "2C", runners_up["D"], "2D"),
        (winners["D"], "1D", best_thirds[4][0], f"3rd-{best_thirds[4][1]}"),
        (runners_up["G"], "2G", runners_up["L"], "2L"),
        (winners["E"], "1E", best_thirds[3][0], f"3rd-{best_thirds[3][1]}"),
        (runners_up["H"], "2H", runners_up["K"], "2K"),
        (winners["F"], "1F", best_thirds[2][0], f"3rd-{best_thirds[2][1]}"),
        (runners_up["I"], "2I", runners_up["J"], "2J"),
        (winners["G"], "1G", best_thirds[1][0], f"3rd-{best_thirds[1][1]}"),
        (winners["H"], "1H", best_thirds[0][0], f"3rd-{best_thirds[0][1]}"),
        (winners["I"], "1I", winners["L"], "1L"),
        (winners["J"], "1J", winners["K"], "1K"),
    ]

    bracket_matches = []
    for i, (standing_a, origin_a, standing_b, origin_b) in enumerate(pairings, 1):
        bracket_matches.append(BracketMatch(
            match_id=i,
            round_name="Round of 32",
            team_a=standing_a.team,
            team_b=standing_b.team,
            team_a_origin=origin_a,
            team_b_origin=origin_b,
        ))

    return Bracket(
        round_of_32=bracket_matches,
        qualified_teams=32,
    )
