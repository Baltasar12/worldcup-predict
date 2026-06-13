from typing import List, Dict

def compute_calibration_bins(predictions: List[Dict], actuals: List[int]) -> List[Dict]:
    """
    Groups predictions into probability bins and computes empirical draw rates.
    predictions: List of dicts with 'home', 'draw', 'away' probabilities.
    actuals: List of actual outcomes (0=Home, 1=Draw, 2=Away).
    """
    bins = [
        (0.0, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.25),
        (0.25, 0.30), (0.30, 0.40), (0.40, 1.0)
    ]
    
    results = []
    for b_min, b_max in bins:
        bin_matches = [
            (p, a) for p, a in zip(predictions, actuals) 
            if b_min <= p["draw"] < b_max
        ]
        
        count = len(bin_matches)
        if count == 0:
            continue
            
        avg_pred_draw = sum(p["draw"] for p, a in bin_matches) / count
        actual_draws = sum(1 for p, a in bin_matches if a == 1)
        actual_draw_rate = actual_draws / count
        
        results.append({
            "bin": f"{b_min:.2f}-{b_max:.2f}",
            "count": count,
            "predicted_prob": avg_pred_draw,
            "actual_prob": actual_draw_rate
        })
        
    return results
