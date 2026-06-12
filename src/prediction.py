"""
Shared prediction utilities.

Single source of truth for match probability calculations.
Used by both the /predict API endpoint and the World Cup simulation engine.
"""

import math
from src.calculate_elo import expected_score


def get_calibrated_draw_prob(rating_a: float, rating_b: float) -> float:
    """
    Empirically calibrated draw probability based on Elo difference.

    Derived from historical match data using a Gaussian fit:
        P(Draw) = 0.2800 * exp(-(diff / 370.0)^2)

    Parameters:
        rating_a: Elo rating of team A.
        rating_b: Elo rating of team B.

    Returns:
        Draw probability as a float between 0 and 1.
    """
    diff = abs(rating_a - rating_b)
    return 0.28 * math.exp(-(diff / 370.0) ** 2)


def get_match_probabilities(
    elo_a: float, elo_b: float
) -> tuple[float, float, float]:
    """
    Decompose Elo expected scores into win/draw/loss probabilities.

    Uses the Elo expected score (which encapsulates Win + 0.5 * Draw)
    combined with the calibrated draw model to produce three distinct
    probabilities that sum to 1.0.

    All matches are treated as neutral venue.

    Parameters:
        elo_a: Elo rating of team A.
        elo_b: Elo rating of team B.

    Returns:
        Tuple of (win_a, draw, win_b) probabilities, normalized to sum to 1.0.
    """
    exp_a = expected_score(elo_a, elo_b, 0)
    exp_b = expected_score(elo_b, elo_a, 0)

    draw_prob = get_calibrated_draw_prob(elo_a, elo_b)

    # P(Win) = Expected - 0.5 * P(Draw)
    win_a = max(0.0, exp_a - 0.5 * draw_prob)
    win_b = max(0.0, exp_b - 0.5 * draw_prob)

    # Normalize to ensure probabilities sum to 1.0
    total = win_a + win_b + draw_prob
    win_a /= total
    win_b /= total
    draw_prob /= total

    return (win_a, draw_prob, win_b)
