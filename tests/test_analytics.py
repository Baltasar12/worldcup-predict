import math
from src.analytics.metrics import calculate_accuracy, calculate_log_loss, calculate_brier_score

def test_accuracy():
    # 0 = Home, 1 = Draw, 2 = Away
    probs = [0.6, 0.3, 0.1]
    assert calculate_accuracy(probs, 0) == 1
    assert calculate_accuracy(probs, 1) == 0
    assert calculate_accuracy(probs, 2) == 0

def test_log_loss():
    probs = [0.8, 0.1, 0.1]
    
    # Correct prediction
    loss_0 = calculate_log_loss(probs, 0)
    assert math.isclose(loss_0, -math.log(0.8), rel_tol=1e-5)
    
    # Incorrect prediction
    loss_1 = calculate_log_loss(probs, 1)
    assert math.isclose(loss_1, -math.log(0.1), rel_tol=1e-5)

def test_brier_score():
    probs = [0.5, 0.3, 0.2]
    
    # Actual is 0 (Home Win)
    # Brier should be ((0.5 - 1)^2 + (0.3 - 0)^2 + (0.2 - 0)^2) / 2
    # = (0.25 + 0.09 + 0.04) / 2 = 0.38 / 2 = 0.19
    score = calculate_brier_score(probs, 0)
    assert math.isclose(score, 0.19, rel_tol=1e-5)
    
    # Actual is 1 (Draw)
    # Brier should be ((0.5 - 0)^2 + (0.3 - 1)^2 + (0.2 - 0)^2) / 2
    # = (0.25 + 0.49 + 0.04) / 2 = 0.78 / 2 = 0.39
    score = calculate_brier_score(probs, 1)
    assert math.isclose(score, 0.39, rel_tol=1e-5)
