"""
Central configuration for the Lotto Prediction Tool.

This file defines:
- Lottery rules
- Analysis windows
- Mode-specific parameters

No logic should live here.
"""

# =========================
# LOTTERY RULES
# =========================

MIN_NUMBER = 1
MAX_NUMBER = 49          # change later if needed
NUMBERS_PER_DRAW = 6     # e.g. 6/49 lottery
INCLUDE_BONUS_NUMBER = False


# =========================
# TREND WINDOWS
# =========================

# Short-term trend window (recent draws)
SHORT_TERM_WINDOW = 20

# Long-term trend window (historical baseline)
LONG_TERM_WINDOW = 200


# =========================
# SIGNAL WEIGHTS
# (initial values, tunable later)
# =========================

WEIGHT_SHORT_TERM = 0.35
WEIGHT_LONG_TERM = 0.25
WEIGHT_HOTNESS = 0.20
WEIGHT_PAIR = 0.20


# =========================
# MODE PARAMETERS
# =========================

# Number Prediction Mode
NUMBER_MODE_PARAMS = {
    "use_pairs": True,
    "min_confidence": 0.0,
}

# Full Line Generation Mode
LINE_MODE_PARAMS = {
    "use_pairs": True,
    "num_lines": 5,
    "enforce_balance": True,
    "randomness_blend": 0.25,  # 0 = fully biased, 1 = fully random
}


# =========================
# LOTTERY PROFILES
# =========================

LOTTERY_PROFILES = {
    "irish_lotto": {
        "min": 1,
        "max": 47,
        "numbers_per_draw": 6,
        "bonus": False,
    },
    "daily_million": {
        "min": 1,
        "max": 39,
        "numbers_per_draw": 6,
        "bonus": False,
    },
    "uk_lotto": {
        "min": 1,
        "max": 59,
        "numbers_per_draw": 6,
        "bonus": False,
    },
    "euromillions": {
        "min": 1,
        "max": 50,
        "numbers_per_draw": 5,
        "bonus": True,
        "bonus_min": 1,
        "bonus_max": 12,
        "bonus_count": 2,
    },
}


 "powerball": {
        "min": 1,
        "max": 69,
        "numbers_per_draw": 5,
        "bonus": True,
        "bonus_min": 1,
        "bonus_max": 26,
        "bonus_count": 1,
    },
    "megamillions": {
        "min": 1,
        "max": 70,
        "numbers_per_draw": 5,
        "bonus": True,
        "bonus_min": 1,
        "bonus_max": 25,
        "bonus_count": 1,
    },
