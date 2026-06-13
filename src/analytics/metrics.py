import math
from typing import List

def calculate_accuracy(probs: List[float], actual_outcome: int) -> int:
    """
    Returns 1 if the highest probability matches the actual outcome, 0 otherwise.
    actual_outcome: 0 for Home Win, 1 for Draw, 2 for Away Win
    probs: [p_home, p_draw, p_away]
    """
    predicted_outcome = probs.index(max(probs))
    return 1 if predicted_outcome == actual_outcome else 0

def calculate_log_loss(probs: List[float], actual_outcome: int) -> float:
    """
    Returns the Categorical Cross-Entropy (Log Loss) for a single match.
    Clamps probabilities to avoid log(0).
    """
    p = max(min(probs[actual_outcome], 1 - 1e-15), 1e-15)
    return -math.log(p)

def calculate_brier_score(probs: List[float], actual_outcome: int) -> float:
    """
    Returns the Brier Score for a 3-way outcome.
    Formula: sum( (p_i - y_i)^2 ) over i=0,1,2.
    """
    brier = 0.0
    for i in range(3):
        y_i = 1.0 if i == actual_outcome else 0.0
        brier += (probs[i] - y_i) ** 2
    # Typically scaled by 0.5 to bound between 0 and 1, but standard definition is sum of squared diffs.
    return brier / 2.0
