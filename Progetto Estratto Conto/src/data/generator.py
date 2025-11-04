# src/data/generator_simple.py
# ------------------------------------------------------------
# Genera dati sintetici compatibili con il classificatore:
# date, amount, category, merchant, day_of_week, is_weekend, month
# ------------------------------------------------------------

from __future__ import annotations
import argparse
import random
import pandas as pd
from datetime import date
import calendar
from pathlib import Path

CATEGORIES = {
    "Restaurant": ["Pizza Place", "Trattoria Roma", "Sushi Bar"],
    "Groceries": ["Supermarket", "Organic Market", "Coop"],
    "Transport": ["Gas Station", "Taxi", "Train Station"],
    "Rent": ["Landlord"],
    "Entertainment": ["Cinema", "Streaming Service", "Concert Hall"],
    "Shopping": ["Clothing Store", "Electronics Shop"],
    "Healthcare": ["Pharmacy", "Clinic"],
    "Utilities": ["Electric Company", "Water Utility", "Internet Provider"],
}


def generate_sample_data(start_year: int = 2024, months: int = 3, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    rows = []
    for m_offset in range(months):
        year = start_year + (m_offset // 12)
        month = (m_offset % 12) + 1
        last_day = calendar.monthrange(year, month)[1]

        for day in range(1, last_day + 1):
            d = date(year, month, day)
            weekday = d.strftime("%A")
            is_weekend = 1 if weekday in ["Saturday", "Sunday"] else 0

            # Numero casuale di transazioni in quel giorno
            n_tx = random.choices([0, 1, 2, 3], weights=[0.2, 0.5, 0.25, 0.05])[0]
            for _ in range(n_tx):
                category = random.choice(list(CATEGORIES.keys()))
                merchant = random.choice(CATEGORIES[category])
                base = random.uniform(10, 200)

                # Logiche di importo base
                if category == "Rent":
                    amount = 1000 + random.uniform(-50, 50)
                elif category == "Utilities":
                    amount = 50 + random.uniform(-20, 20)
                elif category == "Restaurant" and is_weekend:
                    amount = base * 1.3
                elif category == "Shopping" and month == 12:
                    amount = base * 1.5
                else:
                    amount = base

                rows.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "amount": round(amount, 2),
                    "category": category,
                    "merchant": merchant,
                    "day_of_week": weekday,
                    "is_weekend": is_weekend,
                    "month": month,
                })

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Genera dati sintetici di transazioni bancarie.")
    parser.add_argument("--months", type=int, default=3, help="Numero di mesi da generare (default: 3)")
    parser.add_argument("--seed", type=int, default=42, help="Seed casuale per la riproducibilità")
    parser.add_argument("--start-year", type=int, default=2024, help="Anno iniziale (default: 2024)")
    parser.add_argument("--output", type=str, default="../../data/sample_data.csv",
                        help="Percorso file CSV di output (default: ../../data/sample_data.csv)")

    args = parser.parse_args()

    df = generate_sample_data(start_year=args.start_year, months=args.months, seed=args.seed)

    out_path = Path(__file__).resolve().parent / Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")

    print(f"[GEN_SIMPLE] ✅ Generati {len(df)} record in {out_path.resolve()}")


if __name__ == "__main__":
    main()