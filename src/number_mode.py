"""
Number Prediction Mode.

This module provides ranked number recommendations based on
combined bias scores and confidence levels.
"""

from typing import List, Dict


def predict_numbers(
    combined_scores: Dict[int, Dict[str, float]],
    count: int = 1,
    min_confidence: float = 0.0,
) -> List[Dict[str, float]]:
    """
    Predict favored lottery numbers.

    Parameters:
        combined_scores (dict): Output from combine_signals()
        count (int): Number of numbers to return (default = 1)
        min_confidence (float): Minimum confidence threshold

    Returns:
        List[dict]: Ranked number predictions
    """
    # Filter by confidence
    filtered = {
        n: data for n, data in combined_scores.items()
        if data["confidence"] >= min_confidence
    }

    # Sort by score descending
    ranked = sorted(
        filtered.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    results = []

    for n, data in ranked[:count]:
        results.append({
            "number": n,
            "score": data["score"],
            "confidence": round(data["confidence"] * 100, 2),
            "explanation": _explain_number(data),
        })

    return results


def _explain_number(data: Dict[str, float]) -> str:
    """
    Generate a short explanation for a number.
    """
    score = data["score"]

    if score > 0.5:
        return "Strong positive bias across signals"
    elif score > 0.2:
        return "Moderate positive trend detected"
    elif score > 0:
        return "Slight positive bias"
    elif score < -0.5:
        return "Strong negative bias recently"
    elif score < -0.2:
        return "Moderate negative trend"
    else:
        return "Neutral / mixed signals"
