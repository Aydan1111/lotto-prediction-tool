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
