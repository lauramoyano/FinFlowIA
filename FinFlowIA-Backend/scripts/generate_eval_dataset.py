"""
Generate the labeled evaluation dataset used to measure categorization
accuracy (RFC section 8.5 — "Evaluación de Precisión").

Usage:
    python scripts/generate_eval_dataset.py
    python scripts/generate_eval_dataset.py --count 300 --out data/synthetic/my_eval.csv

Output CSV columns: description, amount, transaction_type, expected_category
This is exactly the shape `evaluate_prompts.py` expects.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.synthetic_data import generate_transactions  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).parent.parent / "data" / "synthetic" / "eval_dataset.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=200, help="Number of rows to generate")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducibility")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    args = parser.parse_args()

    transactions = generate_transactions(args.count, seed=args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["description", "amount", "transaction_type", "expected_category"])
        for t in transactions:
            writer.writerow([t.description, str(t.amount), t.transaction_type, t.category])

    print(f"Wrote {len(transactions)} labeled rows to {args.out}")


if __name__ == "__main__":
    main()
