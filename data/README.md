# Historical Draw Data Format

This folder contains historical lottery draw data used by the Lotto Prediction Tool.

All data files must be provided in CSV format and follow the structure defined below.

---

## Required Columns

Each row represents a single draw.

| Column Name | Description |
|------------|------------|
| draw_date | Date of the draw (YYYY-MM-DD) |
| numbers | Comma-separated list of drawn numbers (e.g. "3,12,18,27,34,41") |

---

## Optional Columns

| Column Name | Description |
|------------|------------|
| bonus | Bonus number (if applicable) |
| lottery | Lottery identifier (e.g. uk_lotto, irish_lotto, powerball) |

---

## Notes

- Numbers must be integers
- Order of numbers does not matter
- Validation will enforce lottery rules based on configuration
- Multiple lotteries may coexist in this folder
