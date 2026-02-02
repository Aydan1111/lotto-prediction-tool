"""
Lottery-aware data loading and validation.

Responsibilities:
- Load historical draw CSVs
- Validate draws against lottery profiles
- Parse main and bonus numbers into clean structures
"""

import pandas as pd
from typing import List

from src.config import LOTTERY_PROFILES


REQUIRED_COLUMNS = {"draw_date", "numbers", "lottery"}
OPTIONAL_COLUMNS = {"bonus"}


def load_draw_data(csv_path: str) -> pd.DataFrame:
    """
    Load and validate historical lottery draw data.

    Parameters:
        csv_path (str): Path to CSV file

    Returns:
        pd.DataFrame: Cleaned and validated draw data
    """
    df = pd.read_csv(csv_path)

    _validate_columns(df)
    df = _parse_numbers(df)
    df = _validate_draws(df)

    return df


def _validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _parse_numbers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["numbers"] = df["numbers"].apply(_parse_number_list)

    if "bonus" in df.columns:
        df["bonus"] = df["bonus"].apply(_parse_bonus_list)

    return df


def _parse_number_list(value: str) -> List[int]:
    return [int(n.strip()) for n in str(value).split(",") if n.strip()]


def _parse_bonus_list(value: str) -> List[int]:
    if pd.isna(value):
        return []
    return [int(n.strip()) for n in str(value).split(",") if n.strip()]


def _validate_draws(df: pd.DataFrame) -> pd.DataFrame:
    for idx, row in df.iterrows():
        lottery = row["lottery"]

        if lottery not in LOTTERY_PROFILES:
            raise ValueError(f"Unknown lottery '{lottery}' at row {idx}")

        profile = LOTTERY_PROFILES[lottery]
        numbers = row["numbers"]
        bonus = row.get("bonus", [])

        _validate_main_numbers(numbers, profile, idx)
        _validate_bonus_numbers(bonus, profile, idx)

    return df


def _validate_main_numbers(numbers: List[int], profile: dict, idx: int) -> None:
    if len(numbers) != profile["numbers_per_draw"]:
        raise ValueError(
            f"Row {idx}: Expected {profile['numbers_per_draw']} numbers, got {len(numbers)}"
        )

    for n in numbers:
        if not profile["min"] <= n <= profile["max"]:
            raise ValueError(
                f"Row {idx}: Number {n} out of range ({profile['min']}–{profile['max']})"
            )


def _validate_bonus_numbers(bonus: List[int], profile: dict, idx: int) -> None:
    if not profile.get("bonus", False):
        if bonus:
            raise ValueError(f"Row {idx}: Bonus numbers not expected for this lottery")
        return

    expected = profile["bonus_count"]
    if len(bonus) != expected:
        raise ValueError(
            f"Row {idx}: Expected {expected} bonus numbers, got {len(bonus)}"
        )

    for b in bonus:
        if not profile["bonus_min"] <= b <= profile["bonus_max"]:
            raise ValueError(
                f"Row {idx}: Bonus number {b} out of range "
                f"({profile['bonus_min']}–{profile['bonus_max']})"
            )
