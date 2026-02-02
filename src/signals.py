"""
Bias signal calculations.

This module contains lottery-agnostic bias signals that operate
on validated historical draw data.

Each signal returns a per-number score and does NOT make decisions.
"""

from collections import Counter
from typing import Dict

import pandas as pd

from src.config import SHORT_TERM_WINDOW


def short_term_trend_signal(
    df: pd.DataFrame,
    min_number: int,
    max_number: int,
) -> Dict[int, float]:
    """
    Compute short-term frequency deviation for each number.

    Parameters:
        df (pd.DataFrame): Validated draw data (single lottery)
        min_number (int): Minimum valid number
        max_number (int): Maximum valid number

    Returns:
        Dict[int, float]: Per-number short-term bias scores
    """
    # Use most recent draws only
    recent_df = df.tail(SHORT_TERM_WINDOW)

    # Count number occurrences
    counts = Counter()
    for numbers in recent_df["numbers"]:
        counts.update(numbers)

    total_draws = len(recent_df)
    numbers_per_draw = len(recent_df.iloc[0]["numbers"])

    # Expected frequency under uniform randomness
    expected = (total_draws * numbers_per_draw) / (
        max_number - min_number + 1
    )

    scores = {}

    for n in range(min_number, max_number + 1):
        observed = counts.get(n, 0)
        # Normalized deviation
        scores[n] = (observed - expected) / expected

    return scores



def long_term_trend_signal(
    df: pd.DataFrame,
    min_number: int,
    max_number: int,
) -> Dict[int, float]:
    """
    Compute long-term frequency deviation for each number.

    Parameters:
        df (pd.DataFrame): Validated draw data (single lottery)
        min_number (int): Minimum valid number
        max_number (int): Maximum valid number

    Returns:
        Dict[int, float]: Per-number long-term bias scores
    """
    counts = Counter()
    for numbers in df["numbers"]:
        counts.update(numbers)

    total_draws = len(df)
    numbers_per_draw = len(df.iloc[0]["numbers"])

    expected = (total_draws * numbers_per_draw) / (
        max_number - min_number + 1
    )

    scores = {}

    for n in range(min_number, max_number + 1):
        observed = counts.get(n, 0)
        scores[n] = (observed - expected) / expected

    return scores
