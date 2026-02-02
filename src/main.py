"""
Minimal entry point for the Lotto Prediction Tool.

This script demonstrates:
- Loading historical data
- Running Number Prediction Mode
- Running Full Line Generation Mode
"""

from src.data_loader import load_draw_data
from src.signals import (
    short_term_trend_signal,
    long_term_trend_signal,
    hot_cold_gap_signal,
)
from src.combiner import combine_signals
from src.number_mode import predict_numbers
from src.line_mode import generate_lines
from src.config import LOTTERY_PROFILES


def main():
    # --- USER SETTINGS (edit these) ---
    CSV_PATH = "data/example_draws.csv"  # you’ll add this next
    LOTTERY = "irish_lotto"
    PRESET = "balanced"
    NUM_LINES = 5

    # --- Load & filter data ---
    df = load_draw_data(CSV_PATH)
    df_l = df[df["lottery"] == LOTTERY]

    profile = LOTTERY_PROFILES[LOTTERY]

    # --- Build signals ---
    st = short_term_trend_signal(df_l, profile["min"], profile["max"])
    lt = long_term_trend_signal(df_l, profile["min"], profile["max"])
    gap = hot_cold_gap_signal(df_l, profile["min"], profile["max"])

    combined = combine_signals(st, lt, gap, preset=PRESET)

    # --- Number Mode ---
    print("\n🔢 Number Prediction Mode")
    top_number = predict_numbers(combined, count=1)
    for item in top_number:
        print(item)

    # --- Line Mode ---
    print("\n🎟️ Line Generation Mode")
    lines = generate_lines(
        df=df,
        lottery=LOTTERY,
        preset=PRESET,
        num_lines=NUM_LINES,
        locked_numbers=[],
        enforce_balance=True,
        use_pairs=True,
        seed=42,
    )

    for i, line in enumerate(lines, 1):
        if line["bonus"]:
            print(f"Line {i}: {line['numbers']} + Bonus {line['bonus']}")
        else:
            print(f"Line {i}: {line['numbers']}")


if __name__ == "__main__":
    main()
