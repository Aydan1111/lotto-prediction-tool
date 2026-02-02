"""
Full Line Generation Mode.

Generates full lotto lines based on:
- Combined per-number bias scores
- Preset aggressiveness
- Optional pair co-occurrence boosts
- Optional balance constraints
- Optional locked numbers

Supports bonus balls (EuroMillions, Powerball, Mega Millions) if draw data contains 'bonus'.
"""

from __future__ import annotations

import math
import random
from itertools import combinations
from typing import Dict, List, Tuple, Optional

import pandas as pd

from src.config import LOTTERY_PROFILES
from src.signals import short_term_trend_signal, long_term_trend_signal, hot_cold_gap_signal
from src.combiner import combine_signals


# -------------------------
# Preset parameters
# -------------------------
PRESET_PARAMS = {
    # More randomness, less dominance
    "conservative": {"temperature": 0.9, "randomness_blend": 0.45, "pair_strength": 0.20},
    # Middle ground
    "balanced": {"temperature": 1.2, "randomness_blend": 0.25, "pair_strength": 0.35},
    # More bias, pairs can matter more
    "aggressive": {"temperature": 1.7, "randomness_blend": 0.10, "pair_strength": 0.60},
}


# -------------------------
# Public API
# -------------------------
def generate_lines(
    df: pd.DataFrame,
    lottery: str,
    preset: str = "balanced",
    num_lines: int = 5,
    locked_numbers: Optional[List[int]] = None,
    enforce_balance: bool = True,
    use_pairs: bool = True,
    seed: Optional[int] = None,
) -> List[Dict[str, List[int]]]:
    """
    Generate full lotto lines (and bonus balls if applicable).

    Parameters:
        df (pd.DataFrame): Validated draw data (can contain multiple lotteries)
        lottery (str): lottery key from LOTTERY_PROFILES
        preset (str): conservative | balanced | aggressive
        num_lines (int): number of lines to generate
        locked_numbers (list[int] | None): numbers to force into every line (main numbers only)
        enforce_balance (bool): toggle balance constraints for main numbers
        use_pairs (bool): apply pair co-occurrence boosting during selection
        seed (int | None): random seed for reproducibility

    Returns:
        List[dict]: Each item has {"numbers": [...], "bonus": [...]} (bonus may be empty)
    """
    if seed is not None:
        random.seed(seed)

    if preset not in PRESET_PARAMS:
        raise ValueError(f"Unknown preset '{preset}'. Use: {list(PRESET_PARAMS.keys())}")

    if lottery not in LOTTERY_PROFILES:
        raise ValueError(f"Unknown lottery '{lottery}'. Check LOTTERY_PROFILES in config.py")

    profile = LOTTERY_PROFILES[lottery]
    locked_numbers = locked_numbers or []

    # Filter to single lottery history
    df_l = df[df["lottery"] == lottery].copy()
    if df_l.empty:
        raise ValueError(f"No rows found for lottery='{lottery}' in the provided dataset")

    # Build base combined scores for main numbers
    main_combined = _build_combined_for_pool(
        df_l, profile["min"], profile["max"], preset=preset
    )

    # Pair lifts for main numbers (optional)
    pair_lifts = _compute_pair_lifts(df_l, profile["min"], profile["max"]) if use_pairs else {}

    # Validate locks
    _validate_locks(locked_numbers, profile)

    results: List[Dict[str, List[int]]] = []

    for _ in range(num_lines):
        line_numbers = _generate_single_line(
            combined=main_combined,
            min_n=profile["min"],
            max_n=profile["max"],
            count=profile["numbers_per_draw"],
            preset=preset,
            locked=locked_numbers,
            enforce_balance=enforce_balance,
            pair_lifts=pair_lifts,
            use_pairs=use_pairs,
        )

        # Bonus handling (if applicable)
        bonus_numbers: List[int] = []
        if profile.get("bonus", False):
            bonus_numbers = _generate_bonus_numbers(df_l, profile, preset=preset)

        results.append({
            "numbers": sorted(line_numbers),
            "bonus": sorted(bonus_numbers) if bonus_numbers else [],
        })

    return results


# -------------------------
# Core building blocks
# -------------------------
def _build_combined_for_pool(df_pool: pd.DataFrame, min_n: int, max_n: int, preset: str) -> Dict[int, Dict[str, float]]:
    """
    Compute signals + combine_signals for a given pool (main or bonus).
    Returns dict: number -> {"score": float, "confidence": float}
    """
    st = short_term_trend_signal(df_pool, min_n, max_n)
    lt = long_term_trend_signal(df_pool, min_n, max_n)
    gap = hot_cold_gap_signal(df_pool, min_n, max_n)
    combined = combine_signals(st, lt, gap, preset=preset)
    return combined


def _scores_to_weights(
    combined: Dict[int, Dict[str, float]],
    candidates: List[int],
    preset: str,
    pair_boosts: Optional[Dict[int, float]] = None,
) -> List[float]:
    """
    Convert combined scores into sampling weights with preset shaping and randomness blending.
    pair_boosts: optional dict[number] -> boost in [0, +inf), applied multiplicatively.
    """
    params = PRESET_PARAMS[preset]
    temperature = params["temperature"]
    randomness_blend = params["randomness_blend"]

    # Biased weights via softmax-ish exponentiation
    raw = []
    for n in candidates:
        score = combined[n]["score"]
        # temperature shapes how peaky it gets
        w = math.exp(score * temperature)
        if pair_boosts and n in pair_boosts:
            w *= (1.0 + pair_boosts[n])
        raw.append(w)

    # Blend with uniform weights (honest fallback)
    # uniform weights = 1.0 for each candidate
    blended = []
    for w in raw:
        blended.append((1.0 - randomness_blend) * w + randomness_blend * 1.0)

    return blended


def _weighted_choice_no_replace(candidates: List[int], weights: List[float]) -> int:
    """Choose a single item from candidates given weights (no replacement done by caller)."""
    total = sum(weights)
    if total <= 0:
        # fallback to uniform
        return random.choice(candidates)

    r = random.random() * total
    upto = 0.0
    for item, w in zip(candidates, weights):
        upto += w
        if upto >= r:
            return item
    return candidates[-1]


def _generate_single_line(
    combined: Dict[int, Dict[str, float]],
    min_n: int,
    max_n: int,
    count: int,
    preset: str,
    locked: List[int],
    enforce_balance: bool,
    pair_lifts: Dict[Tuple[int, int], float],
    use_pairs: bool,
) -> List[int]:
    """
    Sequentially generate one line without replacement, optionally applying balance constraints and pair boosting.
    """
    # We'll retry a few times if balance constraints fail
    attempts = 0
    while attempts < 200:
        attempts += 1

        selected = list(dict.fromkeys(locked))  # preserve order, unique
        remaining = [n for n in range(min_n, max_n + 1) if n not in selected]

        # Build line sequentially
        while len(selected) < count:
            # Pair boosts depend on what we've already selected
            pair_boosts = {}
            if use_pairs and selected:
                pair_boosts = _pair_boosts_from_selected(selected, remaining, pair_lifts, preset=preset)

            weights = _scores_to_weights(combined, remaining, preset=preset, pair_boosts=pair_boosts)
            pick = _weighted_choice_no_replace(remaining, weights)

            selected.append(pick)
            remaining.remove(pick)

        # Validate constraints
        if enforce_balance:
            if _passes_balance(selected, min_n, max_n):
                return selected
        else:
            return selected

    # If we fail balance too many times, return last generated (always output something)
    return selected


# -------------------------
# Balance constraints (simple & product-friendly)
# -------------------------
def _passes_balance(numbers: List[int], min_n: int, max_n: int) -> bool:
    """
    Simple balance rules:
    - Odd/even not too skewed
    - Low/high not too skewed (split at midpoint)
    """
    k = len(numbers)
    odds = sum(1 for n in numbers if n % 2 == 1)
    evens = k - odds

    # Allow mild skew: for 6 numbers, allow 2–4 either way.
    if k >= 6:
        if odds < 2 or odds > 4:
            return False

    midpoint = (min_n + max_n) / 2.0
    low = sum(1 for n in numbers if n <= midpoint)
    high = k - low

    if k >= 6:
        if low < 2 or low > 4:
            return False

    return True


# -------------------------
# Locks
# -------------------------
def _validate_locks(locked: List[int], profile: dict) -> None:
    if len(set(locked)) != len(locked):
        raise ValueError("Locked numbers contain duplicates")

    if len(locked) > profile["numbers_per_draw"]:
        raise ValueError(
            f"Too many locked numbers: {len(locked)} > numbers_per_draw ({profile['numbers_per_draw']})"
        )

    for n in locked:
        if not profile["min"] <= n <= profile["max"]:
            raise ValueError(f"Locked number {n} out of range ({profile['min']}–{profile['max']})")


# -------------------------
# Pair analysis & boosting
# -------------------------
def _compute_pair_lifts(df_l: pd.DataFrame, min_n: int, max_n: int) -> Dict[Tuple[int, int], float]:
    """
    Compute a simple pair lift metric:
    lift(a,b) = observed_pair_count / expected_pair_count

    expected_pair_count approximated using independent appearance probabilities per draw:
    expected = total_draws * p(a) * p(b)

    Returns dict[(a,b)] = max(0, lift - 1) capped for stability.
    """
    total_draws = len(df_l)
    if total_draws == 0:
        return {}

    # Count individual appearances per draw (not per occurrence)
    indiv = {n: 0 for n in range(min_n, max_n + 1)}
    pair_counts: Dict[Tuple[int, int], int] = {}

    for nums in df_l["numbers"]:
        unique_nums = sorted(set(nums))
        for n in unique_nums:
            if min_n <= n <= max_n:
                indiv[n] += 1

        for a, b in combinations(unique_nums, 2):
            if not (min_n <= a <= max_n and min_n <= b <= max_n):
                continue
            key = (a, b)
            pair_counts[key] = pair_counts.get(key, 0) + 1

    # Compute lifts
    lifts: Dict[Tuple[int, int], float] = {}
    eps = 1e-9
    for (a, b), observed in pair_counts.items():
        pa = indiv[a] / total_draws
        pb = indiv[b] / total_draws
        expected = total_draws * pa * pb
        lift = observed / (expected + eps)

        # Convert to a stable "excess association" in [0, cap]
        excess = max(0.0, lift - 1.0)
        lifts[(a, b)] = min(excess, 2.0)  # cap prevents dominance

    return lifts


def _pair_boosts_from_selected(
    selected: List[int],
    candidates: List[int],
    pair_lifts: Dict[Tuple[int, int], float],
    preset: str,
) -> Dict[int, float]:
    """
    Convert pair lifts into candidate boosts based on already selected numbers.
    Boost is the sum of excess lifts with selected numbers, scaled by preset strength.
    """
    strength = PRESET_PARAMS[preset]["pair_strength"]
    boosts: Dict[int, float] = {}

    for c in candidates:
        total = 0.0
        for s in selected:
            a, b = (s, c) if s < c else (c, s)
            total += pair_lifts.get((a, b), 0.0)
        if total > 0:
            boosts[c] = total * strength

    return boosts


# -------------------------
# Bonus number generation
# -------------------------
def _generate_bonus_numbers(df_l: pd.DataFrame, profile: dict, preset: str) -> List[int]:
    """
    Generate bonus numbers if the dataset contains bonus history; otherwise use uniform sampling.
    """
    bonus_count = profile["bonus_count"]
    bonus_min = profile["bonus_min"]
    bonus_max = profile["bonus_max"]

    # If no bonus history column exists, fall back to uniform
    if "bonus" not in df_l.columns:
        pool = list(range(bonus_min, bonus_max + 1))
        random.shuffle(pool)
        return pool[:bonus_count]

    # Build a temporary "numbers" view of bonus history so we can reuse signals/combiner
    df_b = df_l.copy()
    df_b["numbers"] = df_b["bonus"].apply(lambda x: x if isinstance(x, list) else [])

    # If bonus entries are empty, fallback uniform
    if df_b["numbers"].map(len).sum() == 0:
        pool = list(range(bonus_min, bonus_max + 1))
        random.shuffle(pool)
        return pool[:bonus_count]

    combined_bonus = _build_combined_for_pool(df_b, bonus_min, bonus_max, preset=preset)

    selected: List[int] = []
    remaining = list(range(bonus_min, bonus_max + 1))

    while len(selected) < bonus_count:
        weights = _scores_to_weights(combined_bonus, remaining, preset=preset)
        pick = _weighted_choice_no_replace(remaining, weights)
        selected.append(pick)
        remaining.remove(pick)
