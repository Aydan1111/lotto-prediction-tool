"""
Signal combination and confidence estimation.

This module combines independent bias signals into a single
probability surface, governed by preset aggressiveness.
"""

from typing import Dict

from src.config import (
    WEIGHT_SHORT_TERM,
    WEIGHT_LONG_TERM,
    WEIGHT_HOTNESS,
)


def _normalize(scores: Dict[int, float]) -> Dict[int, float]:
    """
    Normalize a score dict to the range [-1, 1].
    """
    if not scores:
        return scores

    max_abs = max(abs(v) for v in scores.values()) or 1.0
    return {k: v / max_abs for k, v in scores.items()}


def combine_signals(
    short_term: Dict[int, float],
    long_term: Dict[int, float],
    hot_cold: Dict[int, float],
    preset: str = "balanced",
) -> Dict[int, Dict[str, float]]:
    """
    Combine bias signals into a final score and confidence.

    Presets:
        - conservative
        - balanced
        - aggressive
    """
    short_term = _normalize(short_term)
    long_term = _normalize(long_term)
    hot_cold = _normalize(hot_cold)

    combined = {}

    # Preset multipliers
    if preset == "conservative":
        dominance = 0.7
        randomness_damp = 0.5
    elif preset == "aggressive":
        dominance = 1.4
        randomness_damp = 1.2
    else:  # balanced
        dominance = 1.0
        randomness_damp = 1.0

    for n in short_term:
        raw_score = (
            WEIGHT_SHORT_TERM * short_term.get(n, 0.0) +
            WEIGHT_LONG_TERM * long_term.get(n, 0.0) +
            WEIGHT_HOTNESS * hot_cold.get(n, 0.0)
        )

        # Allow dominance only in aggressive mode
        if preset == "aggressive":
            raw_score *= dominance
        else:
            raw_score = max(min(raw_score, dominance), -dominance)

        confidence = min(abs(raw_score) * randomness_damp, 1.0)

        combined[n] = {
            "score": raw_score,
            "confidence": confidence,
        }

    return combined
