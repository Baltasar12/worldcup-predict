"""
Data models for World Cup simulation.

These are transient simulation structures (not persisted to SQLite).
They represent the output of a single simulation run.
"""

from dataclasses import dataclass, field


@dataclass
class GroupMatch:
    """Result of a single group stage match."""
    team_a: str
    team_b: str
    score_a: int
    score_b: int


@dataclass
class TeamStanding:
    """A team's row in the group standings table."""
    team: str
    points: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    elo: float = 1500.0


@dataclass
class GroupResult:
    """Complete result of a single group's simulation."""
    group_name: str
    standings: list[TeamStanding] = field(default_factory=list)
    matches: list[GroupMatch] = field(default_factory=list)


@dataclass
class BracketMatch:
    """A single knockout fixture in the bracket."""
    match_id: int
    round_name: str
    team_a: str
    team_b: str
    team_a_origin: str  # e.g. "1A", "2B", "3rd-D"
    team_b_origin: str


@dataclass
class Bracket:
    """The complete knockout bracket."""
    round_of_32: list[BracketMatch] = field(default_factory=list)
    round_of_16: list[BracketMatch] = field(default_factory=list)
    quarterfinals: list[BracketMatch] = field(default_factory=list)
    semifinals: list[BracketMatch] = field(default_factory=list)
    final: list[BracketMatch] = field(default_factory=list)
    champion: str = ""
    qualified_teams: int = 0
